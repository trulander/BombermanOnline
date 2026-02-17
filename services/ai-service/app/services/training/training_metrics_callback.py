import logging
from pathlib import Path

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

logger = logging.getLogger(__name__)


class TrainingMetricsCallback(BaseCallback):
    """
    Callback для логирования метрик обучения в TensorBoard.
    
    Отслеживает:
    - last_checkpoint_step - шаг последнего сохранения чекпоинта
    - best_model_step - шаг, на котором была найдена лучшая модель
    - steps_without_improvement - количество шагов без улучшения
    - best_eval_reward - лучшая награда на evaluation окружении
    """

    def __init__(
        self,
        checkpoint_dir: Path,
        eval_log_dir: Path,
        best_model_path: Path,
        verbose: int = 0,
    ) -> None:
        """
        Инициализация callback для отслеживания метрик обучения.
        
        Args:
            checkpoint_dir: Директория с чекпоинтами
            eval_log_dir: Директория с логами evaluation (где хранится evaluations.npz)
            best_model_path: Путь к файлу best_model.zip
            verbose: Уровень детализации логирования
        """
        super().__init__(verbose=verbose)
        self.checkpoint_dir: Path = checkpoint_dir
        self.eval_log_dir: Path = eval_log_dir
        self.best_model_path: Path = best_model_path
        self.last_checkpoint_step: int = 0
        self.best_model_step: int = 0
        self.best_eval_reward: float = float("-inf")
        self.steps_without_improvement: int = 0
        self.last_eval_step: int = 0
        self._last_eval_file_mtime: float = 0.0

    def _on_training_start(self) -> None:
        """Инициализация при начале обучения."""
        # Проверяем наличие best_model при resume training
        # EvalCallback сохраняет best_model в best_model/best_model.zip внутри eval_log_dir.parent
        # Но мы также проверяем наш best_model_path
        if self.best_model_path.exists():
            logger.info(f"Found existing best_model at {self.best_model_path} (resume training)")

    def _on_step(self) -> bool:
        """
        Вызывается на каждом шаге обучения.
        
        Проверяет наличие новых чекпоинтов и обновляет метрики.
        """
        # Проверяем последний checkpoint
        self._update_checkpoint_metric()
        
        # Проверяем best_model из evaluation
        self._update_best_model_metric()
        
        # Логируем метрики
        self._log_metrics()
        
        return True

    def _update_checkpoint_metric(self) -> None:
        """Обновляет метрику last_checkpoint_step, проверяя директорию с чекпоинтами."""
        if not self.checkpoint_dir.exists():
            return
        
        # Ищем все checkpoint файлы
        checkpoint_files = list(self.checkpoint_dir.glob("checkpoint_*_steps.zip"))
        if not checkpoint_files:
            return
        
        # Извлекаем номер шага из имени файла (формат: checkpoint_10000_steps.zip)
        max_step = 0
        for checkpoint_file in checkpoint_files:
            try:
                # Извлекаем число из имени файла
                parts = checkpoint_file.stem.split("_")
                if len(parts) >= 2:
                    step = int(parts[1])
                    if step > max_step:
                        max_step = step
            except (ValueError, IndexError):
                continue
        
        if max_step > self.last_checkpoint_step:
            self.last_checkpoint_step = max_step

    def _update_best_model_metric(self) -> None:
        """Обновляет метрики best_model, читая данные из evaluations.npz."""
        # EvalCallback сохраняет результаты evaluation в evaluations.npz
        evaluations_file = self.eval_log_dir / "evaluations.npz"
        if not evaluations_file.exists():
            return
        
        # Проверяем время модификации файла, чтобы не читать его слишком часто
        try:
            current_mtime = evaluations_file.stat().st_mtime
            if current_mtime <= self._last_eval_file_mtime:
                return
            self._last_eval_file_mtime = current_mtime
        except OSError:
            return
        
        # Читаем данные из evaluations.npz
        try:
            eval_data = np.load(evaluations_file, allow_pickle=True)
            
            # evaluations.npz содержит массивы:
            # - timesteps: массив шагов, на которых проводилась evaluation
            # - results: массив результатов (формат: [episode][evaluation] = reward)
            # - ep_lengths: длины эпизодов
            
            timesteps = eval_data.get("timesteps")
            results = eval_data.get("results")
            
            if timesteps is None or results is None or len(timesteps) == 0:
                return
            
            # results имеет форму (n_evaluations, n_episodes)
            # Вычисляем среднюю награду для каждой evaluation
            mean_rewards = np.mean(results, axis=1) if results.ndim > 1 else results
            
            # Берем последнюю evaluation
            last_idx = len(timesteps) - 1
            current_reward = float(mean_rewards[last_idx])
            eval_step = int(timesteps[last_idx])
            
            # Если нашли лучшую модель
            if current_reward > self.best_eval_reward:
                self.best_eval_reward = current_reward
                self.best_model_step = eval_step
                self.steps_without_improvement = 0
                self.last_eval_step = eval_step
            else:
                # Обновляем steps_without_improvement
                if eval_step > self.last_eval_step:
                    if self.best_model_step > 0:
                        self.steps_without_improvement = eval_step - self.best_model_step
                    self.last_eval_step = eval_step
                    
        except Exception as exc:
            logger.debug(f"Failed to read evaluation results from {evaluations_file}: {exc}")

    def _log_metrics(self) -> None:
        """Логирует метрики в TensorBoard через self.logger.record()."""
        # Логируем метрики через logger.record() для TensorBoard
        self.logger.record("training/last_checkpoint_step", float(self.last_checkpoint_step))
        self.logger.record("training/best_model_step", float(self.best_model_step))
        self.logger.record("training/steps_without_improvement", float(self.steps_without_improvement))
        self.logger.record("training/best_eval_reward", float(self.best_eval_reward))

