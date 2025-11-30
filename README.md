# Generating Random Numbers Using System Peripherals
## By Jelte Oldenhof (s3834069) and Niels Heslenfeld (s2978482)

### rng.py
README for Assignment 2 of the course System and Software Security taught at Leiden University. For this project, we created a random number generator (RNG) that is based on the idea proposed by Hu et al. in "A true random number generator based on mouse movement and chaotic cryptography".

This application implements an RNG that uses mouse movement, keyboard key presses, and system hardware sensor values. The progrma is written in Python and and the used Python version is 3.10.11. The pynput library (version 1.8.1) is used to monitor mouse movement and keyboard key presses (for when the user is active). To gather the information from the system hardware sensors, we use the Python Common Language Runtime (CLR) module from the Python.NET package (pythonnet version 3.0.5). Using CLR (clr_loader version 0.2.8, part of pythonnet), we can load the Open Hardware Monitor software, which is a Dynamic-Link Library (DLL).

Installing pynput and pythonnet is as simple as running:

```
> pip install pynput pythonnet
```

The PyAutoGUI library (version 0.9.54) is used to get the size of the computerscreen used by the user. This can be installed by running:

```
> pip install pyautogui
```

For some simple computations we also make use of the numpy library (version 2.2.2). Install this using:

```
> pip install numpy
```

Before running the program, the Open Hardware Monitor software has to be downloaded from [Open Hardware Monitor software](https://openhardwaremonitor.org/downloads/). Make sure that the download contains the file "OpenHardwareMonitorLib.dll" and that it has permission to run on your computer. Also make sure that the path in "clr.AddReference(r'<PATH>/OpenHardwareMonitorLib')" leads to this file (do not add the .dll).

Now all requirements should be satisfied to run the program. The program is implemented for, and tested on, a Windows based computer. To run the program, one has to run Powershell as an administrator to gain access to all used hardware sensors. Also make sure that you add a folder "data" to the directory with the "rng.py" file. Now, withing the folder with "rng.py", simply execute:

```
> python3 rng.py
```

The program will now start running and the results will be written to the correct .txt files. When you want to exit the program, simply pres "Ctrl+c" and the program will be nicely terminated. You can also see all registered activities of mouse and keyboard in "./data/interactions.csv".

### basic_analysis.py
