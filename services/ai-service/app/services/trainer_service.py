import logging
import random
import time
from collections.abc import Callable
from pathlib import Path

from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecMonitor
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
    StopTrainingOnNoModelImprovement,
)

from app.ai_env.bomberman_env import BombermanEnv
from app.config import settings
from app.logging_config import configure_logging
from app.services.grpc_client import GameServiceGRPCClient
from app.services.training.render_callback import TensorBoardRenderCallback
from app.services.training.training_metrics_callback import TrainingMetricsCallback
from app.services.training.cnn_feature_extractor import BombermanCombinedFeatureExtractor

logger = logging.getLogger(__name__)


MAP_WIDTH = 20
MAP_HEIGHT = 20
ENEMY_COUNT = 10
ENABLE_ENEMIES = True


class TrainingService:
    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
    ) -> None:
        self.grpc_client = grpc_client
        self.model: RecurrentPPO | None = None
        logger.info("TrainingService initialized")

    def start_training(
        self,
        total_timesteps: int = 1000,
        log_name: str = "bomberman_ai",
        enable_render: bool = False,
        render_freq: int = 500,
        model_name: str | None = None,
        enable_checkpointing: bool = True,
        checkpoint_freq: int = 10000,
        enable_evaluation: bool = True,
        eval_freq: int = 2000,
        n_eval_episodes: int | None = None,
        max_no_improvement_evals: int | None = None,
        min_evals: int | None = None,
        use_cnn: bool = True,
        cnn_features_dim: int = 256,
        mlp_features_dim: int = 64,
        features_dim: int = 512,
        count_cpu: int = 20,
        process_startup_delay: float = 0,
    ) -> Path:
        """
        Запускает процесс обучения модели с использованием RecurrentPPO.
        
        Поддерживает периодическое сохранение чекпоинтов, оценку модели на отдельном окружении,
        раннюю остановку при отсутствии прогресса и логирование метрик в TensorBoard.
        
        Args:
            total_timesteps: Общее количество шагов обучения. Определяет длительность обучения.
            
            log_name: Имя для логирования в TensorBoard и организации директорий с чекпоинтами
                и результатами evaluation. Используется для группировки экспериментов.
            
            enable_render: Включить визуализацию игрового процесса. Если True, периодически
                сохраняет кадры игры в TensorBoard для визуального анализа поведения модели.
            
            render_freq: Частота сохранения кадров в TensorBoard (в шагах). Используется только
                если enable_render=True. Определяет, как часто будут сохраняться изображения игры.
            
            model_name: Имя файла модели для дообучения (resume training). Если указан и файл
                существует, обучение продолжится с этой модели. Если None, начинается новое обучение.
                Может быть указан с расширением .zip или без него.
            
            enable_checkpointing: Включить периодическое сохранение промежуточных моделей.
                Если True, модель будет сохраняться каждые checkpoint_freq шагов в директорию
                checkpoints/{log_name}/. Позволяет восстановить обучение с любого чекпоинта.
            
            checkpoint_freq: Частота сохранения чекпоинтов в шагах. Если None, используется
                значение из settings.CHECKPOINT_FREQ (по умолчанию 10000). Рекомендуется устанавливать
                в зависимости от total_timesteps (обычно 10K-50K шагов).
            
            enable_evaluation: Включить периодическую оценку модели и раннюю остановку.
                Если True, модель будет оцениваться на отдельном evaluation окружении каждые
                eval_freq шагов. Лучшая модель автоматически сохраняется. Если False или
                total_timesteps < eval_freq * 2, evaluation отключается (тестовый режим).
            
            eval_freq: Частота оценки модели в шагах. Если None, используется значение из
                settings.EVAL_FREQ (по умолчанию 5000). Определяет, как часто модель будет
                тестироваться на evaluation окружении для определения лучшей версии.
            
            n_eval_episodes: Количество эпизодов для оценки модели. Если None, используется
                значение из settings.N_EVAL_EPISODES (по умолчанию 5). Больше эпизодов дают
                более стабильную оценку, но требуют больше времени.
            
            max_no_improvement_evals: Максимальное количество оценок без улучшения перед
                ранней остановкой. Если None, используется значение из settings.MAX_NO_IMPROVEMENT_EVALS
                (по умолчанию 10). Если модель не улучшается в течение этого количества оценок,
                обучение останавливается автоматически для предотвращения переобучения.
            
            min_evals: Минимальное количество оценок перед проверкой улучшения. Если None,
                используется значение из settings.MIN_EVALS (по умолчанию 5). Гарантирует, что
                ранняя остановка не сработает слишком рано, давая модели время на обучение.
            
            use_cnn: Использовать CNN feature extractor для обработки grid наблюдений.
                Если True, grid данные обрабатываются через CNN, stats через MLP, затем объединяются.
                Если False, используется стандартный MLP для всех наблюдений.
            
            cnn_features_dim: Размерность признаков после CNN обработки grid данных.
                Используется только если use_cnn=True.
            
            mlp_features_dim: Размерность признаков после MLP обработки stats данных.
                Используется только если use_cnn=True.
            
            features_dim: Финальная размерность признаков после объединения CNN и MLP.
                Используется только если use_cnn=True.
            
            count_cpu: Количество параллельных процессов для обучения. Определяет режим векторизации:
                - count_cpu == 1: Используется DummyVecEnv (однопроцессорный режим, текущая реализация).
                  Все окружения выполняются последовательно в одном процессе.
                - count_cpu > 1: Используется SubprocVecEnv (многопроцессорный режим).
                  Каждое окружение выполняется в отдельном процессе, что ускоряет сбор данных.
                  Рекомендуется использовать количество, равное числу CPU ядер или меньше.
            
            process_startup_delay: Задержка между запусками процессов в секундах (используется только при count_cpu > 1).
                Каждый процесс запускается с задержкой, пропорциональной его env_id, чтобы предотвратить
                одновременный выбор одного и того же game-service инстанса всеми процессами.
                Например, при process_startup_delay=0.5: процесс 0 запускается сразу, процесс 1 через 0.5 сек,
                процесс 2 через 1.0 сек и т.д. Это позволяет game-allocator-service обновлять метрики нагрузки
                между запросами и распределять процессы по разным инстансам. По умолчанию 0.5 секунды.
        
        Returns:
            Path: Путь к сохраненной финальной модели. Если был найден best_model в процессе
                evaluation, возвращается путь к best_model, иначе - путь к последней версии модели.
        
        Note:
            - При дообучении (model_name указан) все метрики и счетчики продолжаются с текущего шага
            - В тестовом режиме (total_timesteps < eval_freq * 2) evaluation автоматически отключается
            - Все метрики логируются в TensorBoard: ep_rew_mean, last_checkpoint_step, best_model_step и др.
            - CheckpointCallback сохраняет модели в MODELS_PATH/checkpoints/{log_name}/
            - EvalCallback сохраняет best_model в LOGS_PATH/evaluations/{log_name}/best_model/
        """
        # Use default values from settings if not provided
        checkpoint_freq = checkpoint_freq if checkpoint_freq is not None else settings.CHECKPOINT_FREQ
        eval_freq = eval_freq if eval_freq is not None else settings.EVAL_FREQ
        n_eval_episodes = n_eval_episodes if n_eval_episodes is not None else settings.N_EVAL_EPISODES
        max_no_improvement_evals = (
            max_no_improvement_evals
            if max_no_improvement_evals is not None
            else settings.MAX_NO_IMPROVEMENT_EVALS
        )
        min_evals = min_evals if min_evals is not None else settings.MIN_EVALS
        enable_evaluation = (
            enable_evaluation
            if enable_evaluation is not None
            else settings.ENABLE_EVALUATION
        )

        # Determine if test mode (disable evaluation for short training runs)
        is_test_mode: bool = not enable_evaluation or (total_timesteps < eval_freq * 2)
        if is_test_mode:
            logger.info(
                f"Test mode detected (total_timesteps={total_timesteps} < {eval_freq * 2} "
                f"or enable_evaluation=False), disabling evaluation and early stopping"
            )
            enable_evaluation = False

        logger.info(
            f"Starting training: total_timesteps={total_timesteps}, "
            f"log_name={log_name}, enable_render={enable_render}, "
            f"render_freq={render_freq}, model_name={model_name}, "
            f"enable_checkpointing={enable_checkpointing}, checkpoint_freq={checkpoint_freq}, "
            f"enable_evaluation={enable_evaluation}, eval_freq={eval_freq}, "
            f"use_cnn={use_cnn}, count_cpu={count_cpu}"
        )
        settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Logs path: {settings.LOGS_PATH}, Models path: {settings.MODELS_PATH}")

        render_mode: str | None = "rgb_array" if enable_render else None

        options: dict = {
            "enable_enemies": ENABLE_ENEMIES,
            "seed": 0
        }

        # Create vectorized environment based on count_cpu parameter
        if count_cpu == 1:
            #DummyVecEnv (однопроцессорный режим)
            logger.info("Using DummyVecEnv (single process mode, count_cpu=1)")
            vec_env = DummyVecEnv(
                env_fns=[
                    lambda: BombermanEnv(
                        grpc_client=self.grpc_client,
                        render_mode=render_mode,
                        options=options
                    ),
                ],
            )
        else:
            #SubprocVecEnv (многопроцессорный режим)
            logger.info(
                f"Using SubprocVecEnv (multiprocessing mode, count_cpu={count_cpu}, "
                f"process_startup_delay={process_startup_delay}s) with randomized environment parameters"
            )
            vec_env = SubprocVecEnv(
                env_fns=[
                    make_env(
                        env_id=i, 
                        render_mode=render_mode, 
                        startup_delay=process_startup_delay,
                        options=options,
                    )
                    for i in range(count_cpu)
                ],
                start_method="forkserver"
            )
        
        # Wrap in VecMonitor to track and log episode metrics (ep_rew_mean, ep_len_mean, etc.)
        env = VecMonitor(vec_env)

        # Create separate evaluation environment (if evaluation is enabled)
        # Evaluation always uses DummyVecEnv for stability, regardless of count_cpu
        eval_env = None
        if enable_evaluation:
            logger.info("Creating evaluation environment (always using DummyVecEnv for stability)")
            if count_cpu == 1:
                eval_vec_env = DummyVecEnv(
                    env_fns=[
                        lambda: BombermanEnv(
                            grpc_client=self.grpc_client,
                            render_mode=None,  # No rendering for evaluation
                            options=options
                        ),
                    ],
                )
            else:
                eval_vec_env = SubprocVecEnv(
                    env_fns=[
                        make_env(
                            env_id=i,
                            render_mode=None,
                            startup_delay=process_startup_delay,
                            options=options
                        )
                        for i in range(count_cpu)
                    ],
                    # start_method="spawn"
                )
            eval_env = VecMonitor(eval_vec_env)


        if model_name is None:
            model_name = log_name

        if not model_name.endswith(".zip"):
            model_name = f"{model_name}.zip"

        # Setup base directory for model: MODELS_PATH/{log_name}/
        model_dir = settings.MODELS_PATH / log_name
        model_dir.mkdir(parents=True, exist_ok=True)

        # Setup subdirectories within model_dir
        checkpoint_dir = model_dir / "checkpoints"
        eval_log_dir = model_dir / "evaluations"
        best_model_path = model_dir / "best_model.zip"

        model_file = model_dir / model_name

        resume: bool = False

        # --- Determine whether to resume from an existing model or create a new one ---
        if model_file.exists():
            logger.info(f"Resuming training from existing model: {model_file}")
            self.model = RecurrentPPO.load(
                path=model_file,
                env=env,
                device="auto",
                tensorboard_log=str(settings.LOGS_PATH),
            )
            resume = True
        else:
            logger.warning(
                f"Model file not found at {model_file}, starting fresh training"
            )

        if not resume:
            # Configure policy kwargs based on whether to use CNN
            policy_kwargs = {}
            if use_cnn:
                logger.info(
                    f"Using combined CNN+MLP feature extractor: "
                    f"cnn_features_dim={cnn_features_dim}, "
                    f"mlp_features_dim={mlp_features_dim}, "
                    f"features_dim={features_dim}"
                )
                # MultiInputLstmPolicy passes the entire Dict observation space to the feature extractor.
                # We use BombermanCombinedFeatureExtractor which handles the Dict space correctly:
                # - Processes "grid" key through CNN
                # - Processes "stats" key through MLP
                # - Combines both into a single feature vector
                policy_kwargs = dict(
                    features_extractor_class=BombermanCombinedFeatureExtractor,
                    features_extractor_kwargs=dict(
                        features_dim=features_dim,
                        cnn_features_dim=cnn_features_dim,
                        mlp_features_dim=mlp_features_dim,
                    ),
                    lstm_hidden_size=64,
                    n_lstm_layers=1,
                )
            else:
                logger.info("Using default MLP feature extractor for all observations")
            
            logger.info("Creating new RecurrentPPO model with MultiInputLstmPolicy")
            self.model = RecurrentPPO(
                policy="MultiInputLstmPolicy",
                env=env,
                verbose=0,
                tensorboard_log=str(settings.LOGS_PATH),
                policy_kwargs=policy_kwargs if policy_kwargs else None,
                ent_coef=0.02,
                learning_rate=1e-4,
                n_steps=64,
                batch_size=256
            )

        # --- Callbacks ---
        callbacks = []

        # TrainingMetricsCallback - always enabled to track metrics
        metrics_callback = TrainingMetricsCallback(
            checkpoint_dir=checkpoint_dir,
            eval_log_dir=eval_log_dir,
            best_model_path=best_model_path,
            verbose=0
        )
        callbacks.append(metrics_callback)

        # CheckpointCallback - save intermediate models periodically
        if enable_checkpointing:
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            # In multiprocessing mode, CheckpointCallback interprets save_freq as training steps,
            # not environment steps. So we need to divide by count_cpu to get the correct frequency.
            # For example: if checkpoint_freq=2500 and count_cpu=6, we want checkpoints every 2500 env steps,
            # which means every 2500/6 ≈ 416 training steps.
            checkpoint_save_freq = checkpoint_freq // count_cpu
            checkpoint_callback = CheckpointCallback(
                save_freq=checkpoint_save_freq,
                save_path=str(checkpoint_dir),
                name_prefix="checkpoint",
                save_replay_buffer=False,
                save_vecnormalize=False,
                verbose=0
            )
            callbacks.append(checkpoint_callback)
            logger.info(
                f"CheckpointCallback enabled: saving to {checkpoint_dir} "
                f"every {checkpoint_freq} environment steps "
                f"(every {checkpoint_save_freq} training steps with count_cpu={count_cpu})"
            )

        # EvalCallback and Early Stopping - only if evaluation is enabled
        if enable_evaluation and eval_env is not None:
            eval_log_dir.mkdir(parents=True, exist_ok=True)
            # EvalCallback will create best_model.zip inside model_dir
            # So we pass model_dir directly, and it will create model_dir/best_model.zip

            # Early stopping callback
            stop_callback = StopTrainingOnNoModelImprovement(
                max_no_improvement_evals=max_no_improvement_evals,
                min_evals=min_evals,
                verbose=0,
            )

            # Evaluation callback
            # In multiprocessing mode, EvalCallback interprets eval_freq as training steps,
            # not environment steps. So we need to divide by count_cpu to get the correct frequency.
            # For example: if eval_freq=2000 and count_cpu=6, we want evaluation every 2000 env steps,
            # which means every 2000/6 ≈ 333 training steps.
            eval_callback_freq = eval_freq // count_cpu
            eval_callback = EvalCallback(
                eval_env=eval_env,
                best_model_save_path=str(model_dir),
                log_path=str(eval_log_dir),
                eval_freq=eval_callback_freq,
                deterministic=False,
                render=False,
                n_eval_episodes=n_eval_episodes,
                callback_on_new_best=stop_callback,
                verbose=0
            )
            callbacks.append(eval_callback)
            logger.info(
                f"EvalCallback enabled: evaluating every {eval_freq} environment steps "
                f"(every {eval_callback_freq} training steps with count_cpu={count_cpu}), "
                f"early stopping after {max_no_improvement_evals} evaluations without improvement"
            )

        # Render callback
        if enable_render:
            logger.info("Render enabled — adding TensorBoardRenderCallback")
            callbacks.append(TensorBoardRenderCallback(render_freq=render_freq))

        # --- Training ---
        # reset_num_timesteps=False keeps the global step counter when resuming,
        # so TensorBoard plots continue seamlessly from the previous run.
        logger.info(f"Starting model.learn for {total_timesteps} timesteps (resume={resume})")
        start_time: float = time.monotonic()
        self.model.learn(
            total_timesteps=total_timesteps,
            tb_log_name=log_name,
            callback=callbacks if callbacks else None,
            reset_num_timesteps=not resume,
        )
        elapsed: float = time.monotonic() - start_time
        logger.info(f"Training completed in {elapsed:.2f}s")

        # If resuming, overwrite the same file; otherwise save with log_name.
        self.model.save(path=model_file)
        logger.info(f"Final model saved to {model_file}")
        return model_file


def make_env(
        env_id: int,
        render_mode: str | None = None,
        startup_delay: float = 0.0,
        options: dict = {},
) -> Callable[[], BombermanEnv]:
    """
    Factory function to create environment instances for multiprocessing.

    Each process must have its own isolated instances of dependencies:
    - NatsRepository (with its own NATS connection)
    - GameServiceFinder (with its own NatsRepository)
    - GameServiceGRPCClient (with its own GameServiceFinder)
    - BombermanEnv (with its own GameServiceGRPCClient)

    This ensures that each subprocess in SubprocVecEnv has independent
    connections and doesn't share state with other processes.

    Args:
        env_id: Unique identifier for the environment (used for logging and delay calculation)
        render_mode: Render mode for the environment (None, "rgb_array", etc.)
        startup_delay: Delay in seconds before creating dependencies. Each process waits
            startup_delay * env_id seconds before initialization to prevent simultaneous
            selection of the same game-service instance. Process 0 starts immediately,
            process 1 waits startup_delay seconds, process 2 waits 2*startup_delay, etc.
        options: Base options dictionary with environment parameters
        randomize_params: If True, generates randomized parameters (map_width, map_height, enemy_count)
            for each process based on env_id. Used in multiprocessing mode to train on diverse configurations.

    Returns:
        Callable that creates a BombermanEnv instance when called
    """

    def _init() -> BombermanEnv:
        # Configure logging for this subprocess using existing configuration
        # This ensures logs from child processes are visible
        # from app.config import configure_logging, settings as app_settings
        configure_logging()
        # Get logger after configuration
        logger = logging.getLogger(__name__)
        logger.info(f"[ENV-{env_id}] Subprocess initialized")

        # Add delay before creating dependencies to prevent simultaneous instance selection
        if startup_delay > 0:
            delay = startup_delay * env_id
            logger.info(f"Environment {env_id}: waiting {delay:.2f}s before startup to avoid instance collision")
            time.sleep(delay)

        # Import dependencies inside the function to ensure they're available
        # in each subprocess after fork/spawn
        from app.repositories.nats_repository import NatsRepository
        from app.services.game_service_finder import GameServiceFinder
        from app.services.grpc_client import GameServiceGRPCClient

        # Create isolated dependencies for this process
        # Each process needs its own NATS connection
        nats_repo = NatsRepository(nats_url=settings.NATS_URL)
        # Connect synchronously (NatsRepository.connect() handles async internally)
        nats_repo.connect()

        # Create GameServiceFinder with the isolated NatsRepository
        game_service_finder = GameServiceFinder(nats_repository=nats_repo)

        # Create GameServiceGRPCClient with the isolated GameServiceFinder
        grpc_client = GameServiceGRPCClient(game_service_finder=game_service_finder)

        # Create and return the environment with isolated dependencies
        env = BombermanEnv(
            grpc_client=grpc_client,
            render_mode=render_mode,
            options=options
        )
        logger.info(f"Created environment {env_id} in subprocess with isolated dependencies")
        return env

    return _init