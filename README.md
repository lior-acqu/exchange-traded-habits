# Exchange-Traded Habits
#### Video Demo:  <URL HERE>
#### Description:
##### TL;DR

Exchange-Traded Habits is a web-app built with Flask, HTML, CSS, JS, SQL, and Chart.js. It’s a habit tracker that treats every habit you have entered like an asset that increases in value if you perform the habit and decreases if you don’t.

Feel free to register an account and use it under: https://exchange-traded-habits.vercel.app/

##### Introduction

###### Motivation

I believe that good habits are the key to a happy, healthy, and successful life. Popular books, such as “Atomic Habits” by James Clear, support this view. After reading this exact book, I got the idea of making my own habit tracker.

In “Atomic Habits”, the author James Clear describes habits as continuous improvements of 1%. This means that if your habits make you 1% better each day, you will make enormous improvements over a longer period, such as a year.

The math is simple: If your current self is at 100% and you improve today by 1%, you will be at 101%. In two days, at 102.01%. After a year, you will have improved by a whopping 3778%! This is no magic, just 100% * $1.01^{365}$.

This idea stuck with me. I loved how it sees habits as chances to improve yourself every day. It’s as if the quality of your life were an asset and increased in value when you perform a habit.

This is exactly what I wanted to realize with this project. I wanted to build a habit tracker that visually shows how your habits continuously improve your life, providing a positive feeling and motivation whenever you view it.

##### Technical Implementation

Exchange-Traded Habits is a full-stack web app. It combines multiple technologies and languages.

###### Backend

The backend is built with Flask (Python). It contains the entire logic of handling data, user requests, and user authentication. It is the core of the whole project, ensuring that the data is processed properly for display or storage.

**Files:** app.py

###### Database

The database is hosted on Neon (PostgreSQL, migrated from SQLite). It contains three interconnected tables: users, habits, and habit_logs. Here, all information about the users, their habits, and their daily progress is securely stored.

**Files:** (discontinued, not uploaded) habits.db

###### Frontend

The frontend is built with HTML, CSS, Jinja, and JavaScript. It dynamically displays all data in an appealing format and allows the user to interact with it. The external library Chart.js is used to visualize the data as a graph.

**Files:** ./templates/edit.html, ./templates/index.html, ./templates/layout.html, ./templates/login.html, ./templates/register.html, ./static/index.js, ./static/styles.css

###### Deployment

The app is hosted on Vercel. The platform is very modern and flexible, allowing for seamless deployments. All environment variables (such as secret keys) are also hosted on Vercel.

**Files:** vercel.json, requirements.txt (not uploaded)

##### Features

###### Registration, Login, Logout

The app allows users to create accounts, log in, and log out. All information is processed securely and encrypted if needed (hashed, using werkzeug.security).

###### Adding Habits

Logged in, you can create habits. Each habit will be stored with a title, a short name (based on title), a description, a time interval (how often the habit is performed), and an initial value (formula: $importance * difficulty * ln(interval)$).

###### Habit-Tracking

Each day, an entry is added for each habit automatically. They are added as uncompleted with a decrease in value of 1% (divided by the interval). If you complete a habit, it will increase in value by 1%, compared to yesterday.

###### Main Page

The main page shows all the data in an appealing way. The habits are summarized in a Chart.js graph, showing the total value of a user’s habit “portfolio”. Below the main graph, all habits are listed in a grid. For each habit, you can see its title, value, change in %, and description. Additionally, there are buttons for you to press to:

- complete a habit (Done)
- miss a habit (Missed)
- enter a habit you completed yesterday (Done Yesterday)
- edit the information about the habit (Edit Habit)
- delete the habit (Delete Habit)

###### Editing Habits

When you press the button “Edit Habit” of a habit on the main page, you are taken to another page where you can change the habit’s title, short name, initial value, and description.

That also means that you can make a habit more or less important by increasing its initial value. The increase or decrease in value in % stays the same.

##### Key Decisions

###### Hosting

I chose Vercel for hosting because I made very positive experiences in the past and it is free for projects of such small scope.

###### Design

I went for a dark, simple design with a monospace font to blend in seamlessly with my Notion setup. Notion is an advanced note-taking tool that allows you to embed webpages. This is exactly what I did with Exchange-Traded Habits. In the top-left corner of the main page, you can see text, saying “Built for Notion”. Apart from that, also the buttons are designed to mimic Notion’s aesthetic.

###### Number of Charts

Initially, each habit had its own chart on the main page. However, that resulted in loading times of almost a minute. Thus, I decided to instead only provide one graph, showing the sum of all habits.

###### Colors

I chose a pinkish red for negative values and a slightly greenish blue for positive values. Why? Because I like both colors, especially the blue.

##### Future

The app runs very well. However, there are still some things that can be improved.

One of them is that the app only adds entries for habits if you actually visit the main page on that day. If you don’t, it just skips a day without changing anything about the value of the habits.

To fix that, I am intending to install a cron job that refreshes the page each day.

Apart from that, implementing an AI bot that gives tailored recommendations based on your habits (only on your consent) is a possible path for the future.

Finally, the UX is constantly being simplified and improved.
