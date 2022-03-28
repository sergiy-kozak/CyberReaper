<p align="center">
  <img src="https://freesvg.org/img/grim-reaper.png" width="300">
</p>

<h1 align="center">
  Centralized DDOS (Runner) and MHDDoS (50 Methods)
</h1>

<p align="center">
  <img src="https://img.shields.io/discord/947778619718119434?label=Discord Online&style=for-the-badge">
  <img src="https://img.shields.io/github/last-commit/E-Gideon/CyberReaper?style=for-the-badge">
  <img src="https://img.shields.io/docker/automated/egideon/cyber-reaper?style=for-the-badge">
  <img src="https://img.shields.io/docker/image-size/egideon/cyber-reaper/latest?label=Docker Size&style=for-the-badge">
  <img src="https://img.shields.io/github/repo-size/E-Gideon/CyberReaper?style=for-the-badge">
</p>

## 👀 Корисні посилання
[💸Donate](https://cyberspace.diaka.ua/project)

[👾Discord](https://discord.gg/cyberspace-ua)

[📟Telegram](https://t.me/CyberSpace_UA)

[🖥YouTube](https://www.youtube.com/channel/UCT_I4DRKngHsyHI4SQIdlmQ)

## ❓ Що це:

**Скрипт-обгортка для запуску потужного DDoS інструмента [MHDDoS](https://github.com/MHProDev/MHDDoS)**

- **Не потребує VPN** - автоматично скачує і підбирає робочі проксі для заданих цілей, періодично їх оновлюючи
- Атака **декількох цілей** з автоматичним балансуванням навантаження
- Використовує **різні методи для атаки** і змінює їх в процесі роботи
- Простий та зрозумілий інтерфейс з іменованими параметрами

**🚨ВИМКНІТЬ VPN🚨** - використовуються проксі, VPN тільки заважатиме!

  
## 🚀 Швидкий старт Docker (Рекомендується):

**Встановіть і запустіть Docker**
- [Windows](https://docs.docker.com/desktop/windows/install/)
- [Mac](https://docs.docker.com/desktop/mac/install/)
- [Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

**Виконайте команди у терміналі:**
```
docker pull egideon/cyber-reaper
docker run --rm egideon/cyber-reaper
```

## 🔩 Ручне встановлення (Не рекомендується):
**Встановіть наступний софт:**
- [Git](https://git-scm.com/downloads)
- [Python 3](https://www.python.org/downloads/)

**Виконайте такі команди:**
```
git clone --recurse-submodules https://github.com/E-Gideon/CyberReaper.git
cd CyberReaper\src
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r MHDDoS/requirements.txt
python -m pip install psutil
python main.py
```

## ⚙️ Оновлення CyberReaper (Docker):
**Виконайте таку команду:**
```
docker pull egideon/cyber-reaper:latest
```

## ⚙️ Оновлення CyberReaper (Git):
**Виконайте команди:**
```
cd CyberReaper
git pull
```

## 🧭 Вирішення проблем:
1. Пробели з DNS або пропав інтернет: DNS - це одна з найбільших. Не усі домашні роутери можуть витримати таке навантаження яке робить мережа CyberReaper. Додайте до сток запуску ще один параметер: ```--dns 1.1.1.1``` або ```--dns 8.8.8.8```

    Приклад: ```docker run --rm --dns 1.1.1.1 egideon/cyber-reaper```

2. У консолі з'явилися "трейси" (якась фігня короче 🤔): Це нормально. Інколи це відноситься до нестачі локальних ресурсів, а інколи до успішного "укладення" спати цілі. Система оброблює таки речі, та переходить до наступної цілі.

3. Дядя "**Жор**"а у процессора. Якщо Вас не влаштовує навантаження на процессор, то ось опції:
```
$ docker run -ti --rm --dns 8.8.8.8 egideon/cyber-reaper --help
[19:01:38 - INFO]
  ____      _               ____                         _   _   _   _
 / ___|   _| |__   ___ _ __/ ___| _ __   __ _  ___ ___  | | | | | | / \
| |  | | | | '_ \ / _ \ '__\___ \| '_ \ / _` |/ __/ _ \ | | | | | |/ _ \
| |__| |_| | |_) |  __/ |   ___) | |_) | (_| | (_|  __/ | | | |_| / ___ \
 \____\__, |_.__/ \___|_|  |____/| .__/ \__,_|\___\___| | |  \___/_/   \_\
      |___/                      |_|                    |_|

usage: cyberreaper [-h] [-a MAX_ATTACKS] [-t ATTACK_THREADS_LIMIT] [-c CPU_LIMIT]

optional arguments:
  -h, --help            show this help message and exit
  -a MAX_ATTACKS, --max-attacks MAX_ATTACKS
                        Maximum amount of the attacks executed in parallel (attack pool size).
  -t ATTACK_THREADS_LIMIT, --attack-threads-limit ATTACK_THREADS_LIMIT
                        Limit amount of the threads for every attack. If value >0, it overrules the attack's task configuration 'Threads' parameter provided that has higher value compared to this option's value.
  -c CPU_LIMIT, --cpu-limit CPU_LIMIT
                        Limit the CPU usage by attacks to the specified value.
  --use-proxy, --no-use-proxy
                        Use proxies (default: True)
```

**-a/--max-attacks** - кількість задач, що запускаються одночасно
**-t/--attack-threads-limit** - кількість потоків для кожної з задач
**-c/--cpu-limit** - бажаний CPU Load (загальне значення) у відсотках

Приклад:
```
docker run -ti --rm --dns 8.8.8.8 egideon/cyber-reaper -a 2 -t 10 -c 40
```
Тобто: Дві копії (задачі) по 10 потоків, відтак разом дають 20 потоків, та усе це має поміститися до 40% на процесорі.
**Зверніть увагу** що **для Windows** це значення вимірюється **в одиницях**.


## 💡 FAQs
> **Q:** Як додавати цілі?
>> **A:** Цілі автоматично підтягуються з наших постів.

>**Q:** Навіщо вимикати VPN?
>>**A:** Для атаки використовується Proxy, VPN тільки заважатиме.

>**Q:** Мій реальний IP будуть бачити ті, кого я атакую?
>>**A:** Ні, програмне забезпечення атакує через Proxy.

## ☢️ Дисклеймер:
Це програмне забезпечення створене для тестування навантаження WEB ресурсів. Автори не несуть відповідальності за неправомірне використання

Все що роблять користувачі, ми тільки можемо припустити - що це миротворча операція🙃
