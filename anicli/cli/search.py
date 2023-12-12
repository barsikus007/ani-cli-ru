from contextlib import suppress
from typing import TYPE_CHECKING, List

from eggella.fsm import IntStateGroup
from eggella.command import RawCommandHandler

from anicli import views
from anicli.cli.config import AnicliApp
from anicli._validator import NumPromptValidator, AnimePromptValidator
from anicli._completion import word_completer, anime_word_completer
from anicli.cli.player import run_video

from anicli.cli.video_utils import slice_play_hash, slice_playlist_iter,  is_video_url_valid, \
    get_preferred_quality_index

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseSearch, BaseSource, BaseEpisode
    from anicli_api.player.base import Video


class SearchStates(IntStateGroup):
    START = 0
    EPISODE = 1
    SOURCE = 2
    VIDEO = 3
    SOURCE_SLICE = 4
    VIDEO_SLICE = 5


app = AnicliApp("search")
app.register_states(SearchStates)


@app.on_command("search", cmd_handler=RawCommandHandler())
def search(query: str):
    """find anime titles by query string"""
    app.CTX["search_query"] = query
    app.fsm.run(SearchStates)


@app.on_state(SearchStates.START)
def start_search():
    query = app.CTX["search_query"]
    results = app.CFG.EXTRACTOR.search(query)
    if not results:
        views.Message.not_found()
        return app.fsm.finish()
    views.Message.print_bold("[*] Search:")
    views.Message.show_results(results)
    choose = app.cmd.prompt("~/search ",
                            completer=word_completer(results),
                            validator=NumPromptValidator(results)
                            )
    if choose in ("..", "~"):
        return app.fsm.finish()
    choose = int(choose)
    app.CTX["result"] = results[choose]
    app.fsm.next()


@app.on_state(SearchStates.EPISODE)
def choose_episode():
    result: "BaseSearch" = app.CTX["result"]
    anime: "BaseAnime" = result.get_anime()

    if not anime:
        return app.fsm.prev()

    episodes: List["BaseEpisode"] = anime.get_episodes()
    if not episodes:
        views.Message.not_found_episodes()
        return app.fsm.finish()
    views.Message.print_bold("[*] Episodes:")
    views.Message.show_results(episodes)
    choose = app.cmd.prompt("~/search/episode ",
                            completer=anime_word_completer(episodes),
                            validator=AnimePromptValidator(episodes)
                            )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.START)
    elif choose == "info":
        views.Message.show_anime_full_description(anime)
        return app.fsm.set(SearchStates.EPISODE)

    elif (parts := choose.split("-")) and len(parts) == 2 and all([p.isdigit() for p in parts]):
        span = slice(int(parts[0]), int(parts[1]))
        app.fsm["search"] = {"episode_slice": episodes[span]}
        return app.fsm.set(SearchStates.SOURCE_SLICE)
    else:
        choose = int(choose)
        app.fsm["search"] = {"episode": episodes[choose]}
        app.fsm.set(SearchStates.SOURCE)


@app.on_state(SearchStates.SOURCE)
def choose_source():
    episode: "BaseEpisode" = app.fsm["search"]["episode"]
    sources: List["BaseSource"] = episode.get_sources()
    if not sources:
        views.Message.not_found()
        return app.fsm.prev()

    views.Message.print_bold("[*] Sources:")
    views.Message.show_results(sources)
    choose = app.cmd.prompt("~/search/episode/video ",
                            completer=word_completer(sources),
                            validator=NumPromptValidator(sources)
                            )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()

    app.fsm["search"]["source"] = sources[int(choose)]
    app.fsm.set(SearchStates.VIDEO)


@app.on_state(SearchStates.VIDEO)
def choose_quality():
    source: "BaseSource" = app.fsm["search"]["source"]
    videos = source.get_videos(**app.CFG.httpx_kwargs())
    preferred_quality = get_preferred_quality_index(videos, app.CFG.MIN_QUALITY)

    if not videos:
        views.Message.not_found()
        return app.fsm.prev()

    views.Message.print_bold("[*] Videos:")
    views.Message.show_results(videos)
    choose = app.cmd.prompt("~/search/episode/video/quality ",
                            default=str(preferred_quality),
                            completer=word_completer(videos),
                            validator=NumPromptValidator(videos)
                            )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()
    while 1:
        video = videos[int(choose)]
        if is_video_url_valid(video):
            break
        elif int(choose) == 0:
            views.Message.not_found()
            return app.fsm.set(SearchStates.VIDEO)
        views.Message.video_not_found()
        choose = int(choose) - 1

    app.fsm["search"]["video"] = video
    episode: "BaseEpisode" = app.fsm["search"]["episode"]
    run_video(video, str(episode), player=app.CFG.PLAYER, use_ffmpeg=app.CFG.USE_FFMPEG_ROUTE)
    return app.fsm.set(SearchStates.EPISODE)


@app.on_state(SearchStates.SOURCE_SLICE)
def play_slice():
    episodes: List["BaseEpisode"] = app.fsm["search"]["episode_slice"]
    episode = episodes[0]
    sources: List["BaseSource"] = episode.get_sources()
    views.Message.print_bold("[*] Sources <u>slice mode</u>:")
    views.Message.show_results(sources)
    choose = app.cmd.prompt("~/search/episode/videoS ",
                            completer=word_completer(sources),
                            validator=NumPromptValidator(sources))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.EPISODE)
    else:
        app.fsm["search"]["source_slice"] = sources[int(choose)]
        return app.fsm.set(SearchStates.VIDEO_SLICE)


@app.on_state(SearchStates.VIDEO_SLICE)
def choose_quality_slice():
    first_source: "BaseSource" = app.fsm["search"]["source_slice"]
    episodes: List["BaseEpisode"] = app.fsm["search"]["episode_slice"]
    videos: List["Video"] = first_source.get_videos(**app.CFG.httpx_kwargs())
    preferred_quality = get_preferred_quality_index(videos, app.CFG.MIN_QUALITY)

    views.Message.print_bold("[*] Video <u>slice mode</u>:")
    views.Message.show_results(videos)
    choose = app.cmd.prompt("~/search/episode/videoS/quality ",
                            default=str(preferred_quality),
                            completer=word_completer(videos),
                            validator=NumPromptValidator(videos)
                            )

    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.SOURCE_SLICE)
    while 1:
        video = videos[int(choose)]
        if is_video_url_valid(video):
            break
        elif int(choose) == 0:
            views.Message.not_found()
            return app.fsm.set(SearchStates.SOURCE_SLICE)
        views.Message.video_not_found()
        choose = int(choose) - 1

    cmp_key_hash = slice_play_hash(video, first_source)
    with suppress(KeyboardInterrupt):
        for video, episode in slice_playlist_iter(episodes, cmp_key_hash, app.CFG):
            app.cmd.print_ft("SLICE MODE: Press q + CTRL+C for exit")
            run_video(video, str(episode), player=app.CFG.PLAYER, use_ffmpeg=app.CFG.USE_FFMPEG_ROUTE)
    return app.fsm.set(SearchStates.EPISODE)
