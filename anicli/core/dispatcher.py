from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union, Optional, Callable, Dict, Type

from anicli.core.prompt_loop import PromptLoop
from anicli.core.states import StateDispenser, BaseState
from anicli.core.command import Command
from functools import wraps


# TODO fix store arguments in states
# TODO implement states for commands
# TODO cache result for states (or not?)


class ABCDispatcher(ABC):
    @abstractmethod
    def command(self, keywords: Union[list[str], str],
                meta: Optional[str] = ...,
                *,
                rule: Optional[Callable[..., bool]] = ...,
                state: Optional[BaseState] = ...,
                args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = ...,
                ):
        ...

    @abstractmethod
    def run(self):
        ...


class Dispatcher(ABCDispatcher):
    def __init__(self,
                 loop: PromptLoop,
                 on_close: Callable = lambda: print("Goodbye!")):
        self._commands: list[Command] = []
        self.loop = loop
        self.state_dispenser = StateDispenser()
        self._states: Dict[BaseState, Callable] = {}
        self._on_error_states: Dict[BaseState, Callable[[BaseException], None]] = {}
        self._states_cache: Dict[str, Dict] = {}
        self._on_close = on_close

    def _has_keywords(self, keywords: list[str]) -> bool:
        words = []
        for c in self._commands:
            words.extend(c.keywords)
        return all(k in words for k in keywords)

    def state_handler(self,
                      state: BaseState,
                      on_error: Optional[Callable] = None):
        def decorator(func):
            if not self._states.get(state):
                self._states[state] = func
            if on_error and not self._on_error_states.get(state):
                self._on_error_states[state] = on_error
            return func
        return decorator

    def remove_command(self, keyword: str):
        for i, cls_command in enumerate(self._commands):
            if keyword in cls_command:
                self._commands.pop(i)
                return

    def command(self,
                keywords: Union[list[str], str],
                meta: Optional[str] = None,
                *,
                rule: Optional[Callable[..., bool]] = None,
                state: Optional[BaseState] = None,
                args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = None):
        keywords = [keywords] if isinstance(keywords, str) else keywords

        if self._has_keywords(keywords):
            raise AttributeError(f"command `{keywords}` has already added")

        if not meta:
            meta = ""

        def decorator(func) -> Command:
            nonlocal meta

            if not meta:
                meta = func.__doc__ or ""

            command = Command(loop=self.loop,
                              func=func,
                              meta=meta,
                              state=state,
                              keywords=keywords,  # type: ignore
                              rule=rule,
                              args_hook=args_hook)
            if state:
                self._states[state] = command
            self._commands.append(command)
            return command
        return decorator

    def run(self):
        self.loop.set_dispatcher(self)
        self.loop.load_states(self._states)
        self.loop.load_error_states(self._on_error_states)
        self.loop.load_commands(self._commands)
        try:
            self.loop.loop()
        except (KeyboardInterrupt, EOFError):
            self._on_close()
