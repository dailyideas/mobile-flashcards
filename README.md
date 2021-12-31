# mobile-flashcards

## Table of contents


## Background
It is very common for me to have learnt something, and then forgetting it after a day or two, if the same information does not appear to me repeatedly. Using flashcards may help. However, I'm too lazy to jot things down on physical flashcards. Even if I have written some, I may not have the motivation to pick them up and refresh my memory. Flashcard Apps could be an alternative. I want to have a handy flashcard system which I can add and delete flashcards, and the flashcard system will pop up random flashcards I added from time to time. Instead of searching the App store / Google Play Store for an app that meets my requirements, which are usually too bulky in functionalities, I decided to make one myself. 

The project uses _Docker_ as the platform. _MongoDB_ as the backend to store the flashcards. _Telegram_ as the frontend to interact with the user. Python as the programming language to link everything up. 

## Prerequisites
1. A computer
2. Telegram installed on your phone
3. Basic knowledge of using Python on CLI

## Notices
1. This project was tested on _Ubuntu Focal 20.04_ only. The [_Installation guide_](#Installation-guide) may not be applicable to other versions and Operating systems.

## Installation guide
1. Install Docker Engine.
    - [Offical tutorial](https://docs.docker.com/engine/install/)
1. Manage Docker as a non-root user.
    - Apply to Linux users only
    -  [Offical tutorial](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)
1. Configure Docker to start on boot.
    - Apply to Linux users only
    - [Offical tutorial](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)
1. Install Docker Compose.
    - Apply to Linux users only
    - [Offical tutorial](https://docs.docker.com/compose/install/)
1. Create a new Telegram bot
    - [Offical tutorial](https://core.telegram.org/bots#creating-a-new-bot)
1. Clone this repository to the host machine.
    - [Offical tutorial](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository)
1. Set up `.env`
    - In the project directory, copy `.env.example` and name it as `.env`.
    - Copy and paste the _token_ obtained in "Create a new Telegram bot" after `TG_FLASHCARD_BOT_TOKEN=`.
