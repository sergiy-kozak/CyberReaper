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

## 🧭 Вирішення проблем:
1. Пробели з DNS або пропав інтернет: DNS - це одна з найбільших. Не усі домашні роутери можуть витримати таке навантаження яке робить мережа CyberReaper. Додайте до сток запуску ще один параметер: ```--dns 1.1.1.1``` або ```--dns 8.8.8.8```

    Приклад: ```docker run --rm --dns 1.1.1.1 egideon/cyber-reaper```

2. У консолі з'явилися "трейси" (якась фігня короче 🤔): Це нормально. Інколи це відноситься до нестачі локальних ресурсів, а інколи до успішного "укладення" спати цілі. Система оброблює таки речі, та переходить до наступної цілі.

3. Дядя "**Жор**"а у процессора. Якщо Вас не влаштовує навантаження на процессор, то ось опції:
**2** - кількість запускаємих копій аплікухи
**10** - кількість потоків для кожної з копій
**40** - бажаний CPU Load (загальне значення) у відсотках
```
docker run -ti --rm --dns 8.8.8.8 egideon/cyber-reaper 2 10 40
```
Тобто: Дві копії по 10 тредів мають дати 20 тредів та усе це має поміститися до 40% на процессорі.
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
