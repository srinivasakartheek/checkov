import os
import sys

from tqdm import tqdm

DEFAULT_BAR_FORMAT = '{l_bar}{bar:20}| [{n_fmt}/{total_fmt}] {postfix}'
SLOW_RUNNER_BAR_FORMAT = '{l_bar}{bar:20}| [{n_fmt}/{total_fmt}] [Slow Runner Warning] {postfix}'

SLOW_RUNNERS = {'sca_package'}
LOGS_ENABLED = os.environ.get('LOG_LEVEL', False)


class ProgressBar:
    def __init__(self, framework) -> None:
        self.pbar = None
        self.is_off = not self.should_show_progress_bar()
        self.framework = framework

    def initiate(self, total: int) -> None:
        if total <= 0:
            tqdm.write(f'{self.framework} framework has 0 files to process, no progress bar to show')
            self.is_off = True

        if self.is_off:
            return

        self.pbar = tqdm(total=total, colour=self.get_progress_bar_color(self.framework),
                         bar_format=self.get_progress_bar_format(self.framework), desc=f'[ {self.framework} framework ]')

    def update(self, value: int = 1) -> None:
        if self.is_off:
            return
        self.pbar.update(value)  # type: ignore

    def set_description(self, desc: str) -> None:
        if self.is_off:
            return
        self.pbar.set_description(desc=desc)  # type: ignore

    def close(self) -> None:
        if self.is_off:
            return
        self.pbar.close()  # type: ignore

    def set_additional_data(self, data: dict[str, str]) -> None:
        if self.is_off:
            return
        self.pbar.set_postfix(data)  # type: ignore

    @staticmethod
    def should_show_progress_bar() -> bool:
        if all([not LOGS_ENABLED, sys.__stdout__.isatty()]):
            return True
        return False

    @staticmethod
    def get_progress_bar_color(framework: str) -> str:
        if framework in SLOW_RUNNERS:
            return 'white'
        return 'green'

    @staticmethod
    def get_progress_bar_format(framework: str) -> str:
        if framework in SLOW_RUNNERS:
            return SLOW_RUNNER_BAR_FORMAT
        return DEFAULT_BAR_FORMAT

