import logging
from pathlib import Path

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
        verbose: int = 0,
    ) -> None:
        """
        Инициализация callback для отслеживания метрик обучения.
        
        Args:
            checkpoint_dir: Директория с чекпоинтами
            eval_log_dir: Директория с логами evaluation (где хранится best_model)
            verbose: Уровень детализации логирования
        """
        super().__init__(verbose=verbose)
        self.checkpoint_dir: Path = checkpoint_dir
        self.eval_log_dir: Path = eval_log_dir
        self.last_checkpoint_step: int = 0
        self.best_model_step: int = 0
        self.best_eval_reward: float = float("-inf")
        self.steps_without_improvement: int = 0
        self.last_eval_step: int = 0

    def _on_training_start(self) -> None:
        """Инициализация при начале обучения."""
        # Проверяем наличие best_model при resume training
        best_model_path = self.eval_log_dir / "best_model" / "best_model.zip"
        if best_model_path.exists():
            # При resume пытаемся восстановить информацию о best_model
            # EvalCallback сам восстановит best_reward, но мы можем логировать шаг
            logger.info(f"Found existing best_model at {best_model_path} (resume training)")

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
        """Обновляет метрики best_model, проверяя директорию evaluation."""
        # EvalCallback сохраняет best_model в best_model/best_model.zip
        best_model_path = self.eval_log_dir / "best_model" / "best_model.zip"
        if not best_model_path.exists():
            return
        
        # Проверяем время модификации файла для определения, когда была найдена лучшая модель
        # Но лучше отслеживать через EvalCallback, который логирует eval/mean_reward
        # Здесь мы просто отмечаем, что best_model существует
        
        # Пытаемся прочитать информацию о best_reward из evaluation результатов
        # EvalCallback сохраняет результаты в evaluations/{log_name}/results.csv
        results_file = self.eval_log_dir / "results.csv"
        if results_file.exists():
            try:
                import csv
                with open(results_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    if rows:
                        # Берем последнюю строку (последняя оценка)
                        last_row = rows[-1]
                        if "mean_reward" in last_row:
                            current_reward = float(last_row["mean_reward"])
                            if "timesteps" in last_row:
                                eval_step = int(last_row["timesteps"])
                                
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
                logger.debug(f"Failed to read evaluation results: {exc}")

    def _log_metrics(self) -> None:
        """Логирует метрики в TensorBoard через self.logger.record()."""
        # Логируем метрики через logger.record() для TensorBoard
        self.logger.record("training/last_checkpoint_step", float(self.last_checkpoint_step))
        self.logger.record("training/best_model_step", float(self.best_model_step))
        self.logger.record("training/steps_without_improvement", float(self.steps_without_improvement))
        self.logger.record("training/best_eval_reward", float(self.best_eval_reward))

