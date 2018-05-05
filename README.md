# Sports Item Catalog
This is a python program that serves a web application for managing items in a
catalog. The items can belong to one of several sports themed categories. Users
can log in with either a Facebook or Google account. Once authenticated the user
can create, delete, or update items for any specific category.

This application is intended to be submitted for evaluation as part of the Udacity Fullstack Developer course.

## Getting Started
These instructions provide the necessary steps and resources needed to run the application in a test\dev environment.

### Prerequisites
This software is needed in order to successfully run the application.
The application uses a pre configured virtual machine that has additional necessary resources preinstalled.
- [Vagrant](https://www.vagrantup.com/ "Vagrant Homepage")
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads "VirtualBox Homepage")
- [Udacity FSN Vagrant File](https://github.com/udacity/fullstack-nanodegree-vm "Fullstach Nanodegree Vagrant File GitHub Page")

Other technologies used in this application include Google and Facebook OAuth2 APIs, Bootstrap, CSS, HTML5, Flask, SQLAlchemy

### How to Run
1. Extract files from provided ItemCatalog.zip to vagrant shared folder
2. Start vagrant virtual machine

   ```
   vagrant up
   vagrant ssh
   ```
3. Navigate to vagrant shared folder containing application files

   ```
   cd \vagrant\catalog
   ```
4. Run database_setup.py to setup database and model objects
   ```
   python database_setup.py
   ```
5. Run insertcategories.py to create categories and some default items
   ```
   python insertcategories.py
   ```
6. Run catalog.py to start application
   ```
   python catalog.py
   ```
7. Use browser to navigate to http://localhost:5000/catalog
