"""Модуль загрузки парсера из директории **extractors**"""
from typing import List, cast, Protocol, Type
import importlib
import os


from anicli_ru.base import *


class Extractor(Protocol):
    """Typehints dyn imported extractor"""
    Anime: Type[BaseAnimeHTTP]
    AnimeResult: Type[BaseAnimeResult]
    Episode: Type[BaseEpisode]
    Ongoing: Type[BaseOngoing]
    Player: Type[BasePlayer]
    ResultList: Type[ResultList]


def all_extractors() -> List[str]:
    if __name__ != "__main__":
        dir_path = __file__.replace(__name__.split(".")[-1] + ".py", "") + "extractors"
    else:
        dir_path = "../../extractors"
    return [_.replace(".py", "") for _ in os.listdir(dir_path) if not _.startswith("__") and _.endswith(".py")]


def import_extractor(module_name: str) -> Extractor:
    """
    :param module_name: extractor name
    :return: Imported extractor module
    :raise ImportError:
    """
    try:
        # typehint dynamically import API extractor
        extractor = cast(Extractor, importlib.import_module(module_name, package=None))
    except ModuleNotFoundError:
        raise ModuleNotFoundError(f"Module {module_name} has not founded")
    # check extractor scheme
    for class_ in ("Anime", "AnimeResult", "Episode", "Ongoing", "Player", "ResultList"):
        try:
            getattr(extractor, class_)
        except AttributeError:
            raise AttributeError(f"Module {module_name} has no class {class_}. Did you import extractor?")
    return extractor
