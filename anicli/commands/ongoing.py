import subprocess

from prompt_toolkit import prompt

from anicli.core import BaseState

from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.utils import make_completer, number_validator
from anicli.config import dp


class OngoingStates(BaseState):
    BACK = 0
    ONGOING = 1
    EPISODE = 2
    VIDEO = 3
    PLAY = 4


@dp.state_handler(OngoingStates.PLAY)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    sources = video.get_source()
    print(*[f"[{i}] {s}" for i,s in enumerate(sources)], sep="\n")
    num = prompt("[QUALITY] > ", completer=make_completer(sources), validator=number_validator(sources))
    if num == "..":
        dp.state_dispenser.set(OngoingStates.VIDEO)
        return
    source = sources[int(num)]
    attrs = mpv_attrs(source)
    subprocess.run(" ".join(attrs), shell=True)
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.state_handler(OngoingStates.VIDEO)
def ongoing_video():
    episode: animego.Episode = dp.state_dispenser["episode"]
    videos = episode.get_videos()
    print(*[f"[{i}] {v}" for i, v in enumerate(videos)], sep="\n")
    num = prompt("[VIDEO] > ", completer=make_completer(videos), validator=number_validator(videos))
    if num == "..":
        dp.state_dispenser.set(OngoingStates.EPISODE)
        return
    video = videos[int(num)]
    dp.state_dispenser.update_data({"video": video})
    dp.state_dispenser.set(OngoingStates.PLAY)

@dp.state_handler(OngoingStates.EPISODE)
def ongoing_episodes():
    result: animego.Ongoing = dp.state_dispenser["result"]
    anime = result.get_anime()
    print(anime)
    episodes = anime.get_episodes()
    print(*[f"[{i}] {o}" for i, o in enumerate(episodes)], sep="\n")
    num = prompt("[EPISODE] > ", completer=make_completer(episodes), validator=number_validator(episodes))
    if num == "..":
        dp.state_dispenser.set(OngoingStates.ONGOING)
        return
    episode = episodes[int(num)]
    dp.state_dispenser.update_data({"episode": episode})
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.command("ongoing")
@dp.state_handler(OngoingStates.ONGOING)
def ongoing():
    """search last published titles"""
    ongoings = EXTRACTOR.ongoing()
    if len(ongoings) > 0:
        print(*[f"[{i}] {o}" for i, o in enumerate(ongoings)], sep="\n")
        num = prompt("[ONGOING] > ", completer=make_completer(ongoings), validator=number_validator(ongoings))
        if num == "..":
            dp.state_dispenser.finish()
            return
        dp.state_dispenser.update_data({"result": ongoings[int(num)]})
        dp.state_dispenser.set(OngoingStates.EPISODE)
    else:
        print("Not found")
        dp.state_dispenser.finish()


@ongoing.on_error()
def ong_error(error: BaseException):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        print("ongoing, exit")
        return
