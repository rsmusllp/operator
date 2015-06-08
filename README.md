# Operator

Mobile phone app for use on physical pentests as well as other assessments.
Built for the Android OS using Kivy.

Currently in active development.

## Configuration
Operator uses a basic INI style configuration file. Copy ```config.example.ini``` to ```config.ini``` and set the
values appropriately. To add new configuration options:

 1. Ensure the section already exists in MainApp.build_config
 1. Optionally (and preferably) set a sane default value in MainApp.build_config
 1. Optionally add it to the JSON data used by MainApp.build_settings

## Documentation

Current documentation can be built locally with sphinx using the command:
```sphinx-build -b html docs/source docs/html```.
