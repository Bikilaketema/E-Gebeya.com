# AMET.com - Online Marketplace | Version 2.0

This repository contains the source code for AMET.com | an ideal marketplace that I created for my ALX SWE foundations
program.
https://drive.google.com/file/d/12iy84T6lcRkSJqg2BpBg5FsrK9UQ2Wmx/view?usp=sharing

## NB

This website is totally ideal and it is not an operating company(At least now). The contents in the introduction part of
this README have some ideal issues.

## Author

- [@bikilaketema](https://www.github.com/bikilaketema)

## Introduction

AMET.com aims to solve the problem of providing a user-friendly and efficient online marketplace for individuals and
businesses to buy and sell various products and services. The platform includes features such as user authentication,
product listings, shopping cart functionality, payment integration, a review and rating system, and messaging
capabilities.(Currently not all the features are integrated.)

The project is built using HTML, CSS, and JavaScript for the front-end, and a web framework Flask for the back-end.
Currently the platform is using SQlite 3 database to store it's users info. Version one of it was using firebase to store it's users data but now it's using it's own database. The products listed on the website was being retrived from fakestore's API on version 1.0. But now that is coming from locally stored data using SQLite3. This two are the main improvements in this version.

## Features

- User authentication: Users can create accounts and log in.(Used flask form and Flask login library to implement)
- Product listings: Buyers can see what products are available on the platform.
- Users can buy the product they want from the platform.
- Responsive design: The platform is optimized for desktop and mobile screens using CSS flex box and media query. (Still
  not used any CSS Framework).
- Users can edit their profiles information
- Users can change their password

## Technologies used

- Programming Languages: HTML and CSS(for the frontend), Python(With flask frame work)
- Front-end Framework: CSS Only: with media query and flexbox to make it responsive
- Back-end Framework: Flask
- Database: It's using SQLite3 for database. The database file stored locally...cuz I don't have any server to use for
  that.
- Deployment: Deployed on ubuntu server using NGINX and GUNICORN.(When I was learning SWE foundations @ALX Africa I got
  a server there for free and the website was once deployed on that server. Deploying it and configuring the server was
  an amazing experience. But currently it is not deployed on any active server. But some times I run it on my PC to show
  it to my friends.)

## Usage

Once they open the website, users can perform the following actions:

- Create an account or log in with existing credentials.
- Browse product listings and search for specific items.(Searching is not implemented.)
- Select and click the Purchase button to buy the product they want or see more details about the product by clicking more info.
## NB

This project is underdevelopment. You can download the repo. Create a python3 virtual environement install the
requirements in the env and run the run.py file.
