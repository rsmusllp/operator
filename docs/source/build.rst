How to set up build environment
===============================

Linux is necessary in order to successfully build and deploy Operator.

Kivy
****

`Kivy <http://kivy.org/#home>`_ is the framework for Operator. Kivy is an open source library that allows for the development of Android applications.
Besides Python, Kivy is the most pivotal component of Operator. In order to develop for Operator, fluency in Kivy is important.

To install Kivy, follow `the Kivy instructions <http://kivy.org/docs/installation/installation-linux.html#>`_ (according to whatever OS you are using).

Pay special note to the `"Providing Dependencies" section <http://kivy.org/docs/installation/installation-linux.html#providing-dependencies>`_. It is *very* important that all versions of the dependencies match those specifically listed.

Gmaps
*****

The Kivy Google maps library is the basis for all map integration in Operator. The setup for this is very simple.

To install Kivy GMaps, download the folder "gmaps" from `their official repository <https://github.com/tito/kivy-gmaps>`_. Then place that folder in the main directory of Operator.

Buildozer
*********

`Buildozer <http://buildozer.readthedocs.org/en/latest/>`_ does a lot of the heavy lifting necessary to actually build the .apk file (Android package). It bridges the gap between Python and Java, the native language of the Android architecture.

To install Buildozer, follow `the Buildozer instructions <http://buildozer.readthedocs.org/en/latest/installation.html>`_.

Buildozer relies on a buildozer.init file which contains instructions for the overall characteristics of the application, such as dependencies and orientation. On the Operator repository there will always be an updated buildozer.init, meaning when invoking buildozer it should always be from the main directory of operator (where the init is located).

Furthermore, an updated Android SDK is necessary for Buildozer to run correctly. It will install the SDK automatically on the first run, but it won't succeed until you manually update and install the necessary components from the SDK manager. The manager is located in your home directory at "~/.buildozer/android/platform/android-sdk-21/tools/android".

The necessary packages are::

	Tools/Android SDK Tools
	Tools/Android SDK Platform-tools
	Android 4.0 (API 14)/SDK Platform
	Android 2.2 (API 8)/SDK Platform
	Android 2.2 (API 8)/Google APIs

Although there are some nice simple commands that Buildozer can handle that automates a lot of the process, on some systems it is unreliable due to the nature of ADB servers. It is worth trying the command::
	
	buildozer -v android debug deploy run logcat 

However, should you ever run into issues with that command, the following command sequence is a very reliable alternative::

	adb uninstall com.ss.operator
	buildozer -v android debug
	cd bin
	adb install SecureStateOperator-0.0.1-debug.apk
	cd ..
	adb shell monkey -p com.ss.operator -c android.intent.category.LAUNCHER 1
	adb logcat | grep python

Saving that sequence as a shell script makes the building process very fast and simple.
