# anicli-ru
___
Небольшой скрипт для поиска и просмотра аниме из терминала с русской озвучкой для *unix систем, написанный на python.

Парсит аниме с сайта [animego.org](https://animego.org/) 

Видеоплеер kodik **не поддерживает**, так как у него запросы с видео шифруется **AES**, 
поэтому не все сериалы в необходимом дубляже получится посмотреть.
___
**Install:**

```
git clone https://github.com/vypivshiy/ruanimecli.git
cd ruanimecli
sudo make
```

___
#Usage:
`./anicli-ru`
___
#Commands:
```
q [q]uit - выход из программы
b [b]ack next step - возвратиться на предыдущий шаг
h [h]elp - вывод списка команд
f [f]ind anime by name - поиск аниме по названию (или при нахождении в главном меню "m >" сразу вводить название)
c [c]lear - очистить консоль
```
___
# TODO:
* добавить поддержку proxy;
* выбор качества видео;
* вывод вышедших на сегодняшнюю дату онгоингов;

Для использования скрипта в windows необходимо установить python 3.5+ версии и заменить в коде плеер, например, на vlc

