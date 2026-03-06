# Overview of the Structure of Software and Data Related to Our Experiments

# Summary of Our Lab’s Research

*“Using the cerebellar and vestibular circuitry to understand the logic of neural learning algorithms.”*

The computations performed by our neural circuits in support of sensation, action, and cognition are powerfully shaped by the patterns of synaptic connections between neurons.  This synaptic connectivity is not static, but is continuously changing.  The patterns of activity in a neural circuit, elicited by our experiences, can trigger a strengthening or weakening of specific synapses within the circuit.  This synaptic plasticity underlies our ability to learn from experience. We are analyzing the neural learning rules governing the local “decisions” each synapse in a circuit makes on a moment-by-moment basis about whether to alter its strength, based on its pattern of input.  Ultimately, our goal is to understand how these local decisions are coordinated throughout a neural circuit to yield an algorithm for the adaptive regulation of the circuit’s function.

Our research leverages the simplicity of the circuit architecture in a brain region called the cerebellum, which makes systematic analysis of the function of this circuit experimentally and analytically tractable. We have developed a battery of behavioral paradigms in mice for studying the vestibular control of behavior and its adaptive regulation by the cerebellum, including learned changes in the amplitude and timing of movements, the generalization of learning, and factors influencing the persistence of memory. We are addressing these issues by combining our expertise in analyzing neural circuits using electrophysiological, behavioral, and computational approaches with powerful molecular-genetic tools for precisely manipulating specific neurons or synapses in vivo.

An understanding of the algorithms that neural circuits use to tune their own performance as they compute can guide the design of machines with computing and learning capacity more closely approximating humans, and will enable us to optimize learning in health and in neural circuits damaged by injury or disease.

Our lab currently focuses primarily on two types of experiments that investigate the cerebellum’s role in tuning/training the gain of the vestibular-oculomotor reflex (VOR), optokinetic reflex (OKR), and/or oculomotor integrator: Behavioral and Slice Physiology.

# Behavioral Experiments

Nearly all of our behavioral experiments typically use a rig that consists of two concentric, motorized cylinders: an inner motor (the “stage” or "chair") that moves the animal, and an outer motor (the "drum") that moves the visual world. The rig is also both lightproof and soundproof, to isolate it as much as possible from the outside world, and LED lights are installed inside of the rig (which can be turned on and off from outside of the rig) that can be turned on to illuminate the drum at desired intervals of the experiment.

The "chair" is the inner component that holds the animal. Its purpose is to stimulate the vestibular system (semicircular canals) without any visual cues (unless the drum is also lit by the interior LED lights). The chair is affixed to a high-torque rotary motor that allows it to horizontally rotate the chair (and the mouse’s body) clockwise or counterclockwise.

The "drum" is the outer component that surrounds the mouse. Its purpose is to stimulate the optokinetic system (visual motion detection). The drum is a large cylindrical shell made of opaque material that lowers over the mouse like a dome (the mouse sits in the exact center of this cylinder). The inside of the drum is lined with a high-contrast pattern of black and white vertical stripes (square wave grating).

We can perform a wide variety of training paradigms by independently controlling the velocity profiles of the drum and chair—using waveforms such as sinusoids, steps, or sum-of-sines—to manipulate the visual-vestibular mismatch. Experimental protocols generally follow a block-design structure, consisting of stimulation epochs of predetermined duration separated by 10-second inter-block intervals in darkness. To maintain animal alertness, a brief light flash is presented midway through each rest interval. A typical session begins with 1–3 pre-training baseline assessment blocks ('Pre-tests'), followed by a sustained training phase, and concludes with 1–3 post-training assessment blocks ('Post-tests'). In some variations, intermediate assessment blocks ('Tests') are interleaved throughout the training phase (e.g., after every Nth training block) to track the time course of learning.

Eye movements are recorded using a magnetic eye tracking system (Payne and Raymond, 2017). A small neodymium magnet (0.75×1.5 mm) is surgically implanted beneath the temporal conjunctiva of the \[right/left\] eye. A magnetic field sensor (HMC1512) is rigidly mounted to the head post assembly of the mouse, positioned approximately 3–5 mm lateral to the eye. As the eye rotates, the magnet alters the angle of the magnetic field detected by the sensor, generating a pair of voltage signals linearly related to eye position. The resulting voltage signals are routed through a pre-amplifier located near the sensor to minimize electrical noise, and then transmitted to a CED Power1401 interface (Cambridge Electronic Design). Data is acquired and digitized at a sampling rate of 1 kHz using Spike2 software version 10 (provided by CED).

To calibrate the magnetic sensor voltage to degrees, we utilize a simultaneous video-based validation method. We position a pair of USB 2.0 stereo-cameras, each equipped with an infrared LED affixed above the lens, to capture the eye and generate distinct corneal reflections (CRs) on the recorded image. The calibration protocol consists of a 1 Hz sinusoidal vestibular rotation (e.g., 5-minute duration) driven by the Spike2 software, which continuously records the magnetic eye signal. Immediately upon protocol initiation, a custom MATLAB script triggers simultaneous image acquisition from the stereo-cameras at approximately 30 frames per second, generating nearly-synchronized image stacks for the left and right views. Offline, we analyze the video data using a MATLAB tracking script that identifies the centroids of the pupil and the two corneal reflections (CRs) in each frame. By calculating the geometric relationship between the pupil and the CRs from both camera angles, we derive the true horizontal eye position \[in degrees\]. Finally, we regress the recorded magnetic voltage signal against this video-derived position trace to establish a linear conversion factor (Volts/Degree).

## File and Folder Structure of a Typical Experiment and Calibration (as of January 2026\)

The recording files of an experiment will typically be saved in some folder whose name and location is designated by the researcher (I will use “foldername” for the examples in this section). After the experimental protocol script is finished running in the Spike2 software, the recording (as of January 2026\) is saved in both SMRX (64-bit) and SMR (32-bit) file formats with the same as the folder it’s saved into. Since the MATLAB scripts (provided by CED) we would use to import Spike2 SMRX files are difficult to set up, we use an older MATLAB script (also provided by CED) to import Spike2 SMR files into MATLAB. The requirement for the files to be the same name as the folder is an unfortunately limitation imposed by our custom MATLAB script we use to run a pre-defined analysis of the experiment. The example experiment folder “foldername” should contain the following files after an experiment:

* foldername/foldername.smr  
* foldername/foldername.smrx  
* foldername/foldername.s2rx (additional configuration file for Spike2 software)

The Spike2 files of the corresponding calibration to the experiment will typically be saved in its own folder, within the experiment folder, with the same name appended by the term “\_cali”. This naming requirement is also an unfortunately limitation imposed by our own custom MATLAB scripts. The image stacks corresponding to the collected images from each camera are also saved in this “\_cali” folder as TIFF files (typically named “img1.tiff” and “img2.tiff”), as well as a MAT file (typically named “time.mat”) that contains data generated by the MATLAB script during image collection. A single full frame image is captured from each USB camera as TIFF images (typically named “img1large.tiff” and “img2large.tiff”) to show the setup of the calibration. The example calibration folder should contain the following files after calibration:

* foldername/foldername\_cali/foldername\_cali.smr  
* foldername/foldername\_cali/foldername\_cali.smrx  
* foldername/foldername\_cali/foldername\_cali.s2rx  
* foldername/foldername\_cali/time.mat  
* foldername/foldername\_cali/img1.tiff  
* foldername/foldername\_cali/img2.tiff  
* foldername/foldername\_cali/img1large.tiff  
* foldername/foldername\_cali/img2large.tiff

Key issues that need to be addressed regarding these file and folder structures:

* Project file and folder structures vary between researcher-to-researcher, and can even vary from project-to-project for the same researcher. This makes data management and sharing very difficult, or even impossible.  
* Files used for calibration use filenames that are the same from experiment-to-experiment (e.g. “time.mat”, “img1.tiff”, etc.).  
* It is incompatible with both the Neurodata Without Borders (NWB) and Brain Imaging Data Structure (BIDS) file formats.  
* We need an efficient method of converting 64-bit Spike2 SMRX files to a unified file format (like NWB). This will not only eliminate the need of using the Spike2 file format (difficult to work with), but also eliminate the need to save the additional 32-bit SMR file.

## Overview of Channels Within Spike2 Files

In general, a Spike2 SMR or SMRX recording file will typically contain around 13 channels, but can range from anywhere between 9 to 18 channels (depending on the protocol). The given channel titles, descriptions, and types for our typical 13 channels are as follows:

* “HTVEL” (Horizontal Target Velocity): Velocity *command* signal sent from Spike2 to the drum motor via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “HHVEL” (Horizontal Head Velocity): Velocity *command* signal sent from Spike2 to the chair motor via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “htpos” (Horizontal Target Position): Position *feedback* signal coming from the drum motor to Spike2 via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “hhpos” (Horizontal Head Position): Position *feedback* signal coming from the chair motor to Spike2 via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “hepos1” (Horizontal Eye Position 1): Amplified eye position signal coming from the first channel of the magnetic field sensor to Spike2 via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “hepos2” (Horizontal Eye Position 2): Amplified eye position signal coming from the second channel of the magnetic field sensor to Spike2 via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “htvel” (Horizontal Target Velocity): Velocity *feedback* signal coming from the drum motor to Spike2 via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “hhvel” (Horizontal Head Velocity): Velocity *feedback* signal coming from the chair motor to Spike2 via the Power1401 interface. This will be set up as either a waveform or RealWave channel in Spike2.  
* “TTL1” (Transistor-Transistor Logic 1): Event-related signal (either on or off) that corresponds to when the LED light inside the rig is on (high) or off (low). This will be set up as a “level” event channel in Spike2.  
* “TTL2” (Transistor-Transistor Logic 2): Event-related signal (either on or off) that corresponds to when optogenetic stimulation is being delivered through optical fiber 1\. This will be set up as a “level” event channel in Spike2.  
* “TTL3” (Transistor-Transistor Logic 3): Event-related signal (either on or off) that corresponds to when optogenetic stimulation is being delivered through optical fiber 2\. This will be set up as a “level” event channel in Spike2.  
* “TextMark”: Channel that is a combination of marker and text string data, each of which is stored as a time and 4 bytes of marker information followed by a text string that can be up to 80 characters long. This channel is used in our protocols to annotate key times of the recording with potentially useful data.  
* “Keyboard”: Channel consists of marker data that was used during the protocol, each of which is stored as a time and 4 bytes of marker information.

## Calibration Protocol Scripts and Its Generated Files (as of January 2026\)

We have two sets of scripts to acquire the necessary calibration data for an experiment:

* A set of custom scripts for Spike2 facilitate the calibration protocol that drives the chair motor to perform a 1 Hz sinusoidal VOR stimulation in the dark, while simultaneously recording the eye position signals coming from the magnetic field sensors.  
* A set of custom scripts for MATLAB facilitate the acquisition of image frames from our stereo-cameras while the VOR stimulation is running. MATLAB variables “time1” and “time2” collect the timestamps for the image frames from each camera respectively (note these timestamps are not perfectly accurate due to limitations of MATLAB software and USB cameras).

General procedure for acquiring calibration data for an experiment:

1. Set up the mouse in the rig with the USB stereo-cameras.  
2. In MATLAB, our “runEyeCalibration.m” script is executed to initialize the USB cameras and ready them for capturing image frames. Once ready, a pop-up window in MATLAB tells the researcher to press the “OK” button when the calibration protocol in Spike2 is running.  
3. In Spike2, our calibration protocol script is loaded and executed to begin the 5 minutes of VOR stimulation in the dark.  
4. Immediately after starting the calibration protocol in Spike2, the researcher will press the “OK” button on the MATLAB pop-up window to begin acquisition of image frames from the USB cameras.  
5. When finished, MATLAB will automatically save the acquired images as TIFF files (as well as the corresponding timestamps for the images as a “time.mat” MATLAB file) and the researcher will need to manually save the recording in Spike2 as both an SMR and SMRX file.  
6. If for whatever reason the researcher feels that it was a poor calibration run, they will repeat these steps for additional runs until the researcher is satisfied with the results (however it usually only takes a single run to get a decent calibration).

Key issue that needs to be addressed regarding this method for acquiring calibration data:

* Requires researchers to manually manage the operation of both Spike2 and MATLAB software which allows for opportunities of user error and non-uniformity of calibration data between experiments.

## Calibration Analysis Scripts and Its Generated Files (as of January 2026\)

To calculate the necessary linear conversion factor needed to convert the eye position signal from our magnetic field sensor from Volts to degrees, we run our custom calibration analysis MATLAB application (file is named “eyeCalAnalysis.mlapp”) on the folder containing the calibration data we wish to analyze. We developed this application using MATLAB’s App Designer tool to serve as a simple Graphical User Interface (GUI) that our researchers can use to easily analyze their calibration data. Our app performs calibration analysis in the following steps:

1. A folder browser pop-up window allows the researcher to select the folder that contains the calibration data they wish to analyze.  
2. The calibration data from the selected folder is loaded into the workspace. This includes the stack of image files from the “img1.tiff” and “img2.tiff” files, the image frame timestamp information from the “time.mat” file, and the channel data from the calibration Spike2 SMR file.  
3. Eye pupil position tracking is performed on the set of image frames from the first camera (i.e. “img1.tiff”).   
   1. For the first frame of the sequence of images of the first camera, the researcher manually provides the approximate location of the centroid of the pupil, a single region of interest (ROI) to search for the pupil in the set of image frames, and a single ROI to search for the pair of corneal reflections in the set of image frames.  
   2. The researcher then sets the parameters for the pupil tracking algorithm (e.g. bottom/top image contrast, spot mask radius, pupil radius limit, edge feature threshold, minimum number of features, etc.). The pupil tracking algorithm first applies preprocessing (e.g. resizing the image, Gaussian filter, image contrast based on provided parameters, applying the provided ROI for pupil tracking). Then it loops through each image in the sequence, where for each image:   
   3. The researcher then sets the parameters for the corneal reflection (CR) tracking algorithm (e.g. bottom/top image contrast, CR radius limit).  
   4. The pupil and corneal reflection tracking algorithm is started, which loops through each image in the sequence, where for each image:  
      * It uses a circular hough transform to find circular features within the image, that satisfy the search parameters previously provided by the researcher, and then those candidates are then further filtered for duplicates and other criteria.  
      * Information related to the location of the centroid and radius of each corneal reflection is then extracted as data points.  
      * The brightest regions of the image are masked out (e.g. corneal reflections).  
      * It uses a radial symmetry transform to calculate a best estimate for the centroid of the pupil as an initial guess.  
      * Using this initial guess, it then uses a Starburst algorithm to provide a set of candidates for the locations of the pupil’s edge.  
      * A Random Sample Consensus (RANSAC) based ellipse fitting algorithm is used on the set of pupil edge candidate locations provided by the Starburst algorithm.  
      * This fit is then further refined using a least squares criterion.  
      * Information related to the location of the pupil centroid and radius is then extracted as data points.  
      * Three subplots on the GUI are updated with the results of the current image. The first subplot shows an overlay of the current image, the location of the centroids for the detected pupil and corneal reflections, and the fits for the pupil and corneal reflection boundaries. The second subplot shows a time series line plot of the collection of detected pupil and CR positions over time. The third subplot shows a time series line plot of the collection of calculated pupil and CR radii over time.  
4. Eye pupil position tracking is performed on the next set of image frames from the second camera (i.e. “img2.tiff”).  
5. The results are reviewed by the researcher and individual frames with poor detection can be manually corrected. If the researcher feels that the calibration is so poor that it is effectively unusable, they may decide to abandon this set of calibration data and perform another run of the calibration protocol to get a potentially better set of calibration data.  
6. If the results are satisfactory, the geometric relationship between the pupil and the CRs from both camera angles are calculated to derive the “true” horizontal eye position data, which we often refer to as the “video” eye position data/trace. The video eye position data is then upsampled to match the sample rate of the eye position channel data (e.g. “hepos1” and “hepos2” channels) that was extracted from the Spike2 file (which we often refer to as the “magnet 1” and “magnet 2” eye position data/traces respectively) which is usually 1000 Hz.   
7. A low-pass Butterworth filter is applied to the video and magnet eye position data, a Savitzky-Golay filter is used to derive the corresponding velocity traces, which are then aligned in time using a cross-correlation function.  
8. A saccade-detection algorithm is then applied to the video and magnet data to generate a mask of the locations of saccades to improve the accuracy of the calculation of metrics like VOR gain, signal linearity, etc. This mask is then used with sinusoidal fitting to determine which of the two magnet channel data provide the strongest signal when compared to an ideal sinusoidal function. This sinusoidal fit also provides an estimate of the VOR gain corresponding to each magnet channel in units of Volts. This is used to calculate the needed linear conversion factor for each magnet channel (set to variables named “scaleCh1” and “scaleCh2” respectively). The index of the “better” channel is also set to a variable, and the workspace is saved as a MAT file for use during experiment analysis.  
9. A final set of analyses are performed to visualize and characterize the linearity between the position and velocity data from the magnet channels with that of the video data. The plots and results of these analyses are saved as a set of PDF and MATLAB FIG files.

 After running the calibration analysis MATLAB application, the example calibration folder should contain the following additional files:

* Four MAT files that contain various information used during the calibration analysis and generated upon its completion.  
* Six MATLAB FIG figure files of the results from the various analyses that were performed.  
* Six PDF files that are simply the PDF versions of the same six MATLAB figures.

Key issue that needs to be addressed regarding our calibration analysis:

* Accuracy of the eye tracking algorithm is highly sensitive to the combination of parameters provided by the researcher. Currently, we use a default set of parameters, wait as the tracking algorithm loops through the sequence of images, and decide how well the eye tracking algorithm performed after it's done. If we decide the results are sub-optimal, which is often the case, we may repeat multiple iterations of this until we get results that we are satisfied with. Since the algorithm needs to loop through each image one-by-one in series, this can be a very time consuming process. We need a more efficient method for finding the most optimal parameters for eye tracking.  
* This analysis results in the generation of multiple additional files that become mixed in with the raw calibration data.  
* This GUI is developed using MATLAB’s App Designer tool which saves the application as a MLAPP file. This file type cannot be searched, read, or opened in any IDE (e.g. Visual Studio Code) which makes version control between commits to our Github repository very difficult. Ideally, this application should instead be developed in Python, or at the very least, using a simple MATLAB “.m” script.

## Experiment Analysis Scripts and Its Generated Files (as of January 2026\)

To perform analysis on the set of data from an experiment, we developed another custom MATLAB GUI application (file is named “VOR\_GUI\_App.mlapp”) using App Designer. Our app performs experiment analysis in the following steps (I will use a typical VOR experiment as an example):

1. A folder browser pop-up window allows the researcher to select the folder that contains the experiment data they wish to analyze.  
2. A file browser pop-up window allows the researcher to select the MAT file generated by the calibration analysis that contains the value of the final calculated linear conversion factor of the “best” magnet channel.  
3. Various interactive UI components allow the researcher to set parameters used for the experiment analysis. This includes:  
   1. Checkboxes that correspond to which set of plots and figures the researcher would like to be saved in the experiment data folder at the end of the analysis.  
   2. A dropdown box that allows the researcher to select the type of experiment analysis that they would like the application to perform.  
   3. Numerical fields that allow the researcher to change the default values for parameters used (i.e. low-pass filter cutoff frequency, saccade detection algorithm threshold, Savitzky-Golay filter window size, etc.).  
4. Pressing a “GO” button starts the experiment analysis and any encountered issues/errors are displayed in the MATLAB console.  
5. Data from the calibration analysis MAT files and channel data from the experiment Spike2 SMR file are loaded into the workspace.  
6. All of this data, along with data related to the parameters that were set by the researcher in the GUI, are passed as arguments to another script that corresponds to the type of experiment analysis the researcher selected on the GUI dropdown component.  
7. The linear conversion factor of the “best” magnet channel is loaded to a “scaleCh” variable.  
8. The start and end times of each block (e.g. pretest, training, test, posttest) in the experiment are extracted from the Spike2 data.  
9. An “hepos” variable is defined as the channel data corresponding to the “best” magnet channel with the linear conversion factor applied to convert it into the proper units of degrees.  
10. Respective variables for the drum (“htvel”) and chair (“hhvel”) velocity channels are also defined.  
11. The analysis then loops through each block of the experiment, where for each block:  
    1. The segment of data between the start and end times of the block for “hepos”, “htvel”, and “hhvel” are extracted into temporary variables.  
    2. A low-pass Butterworth and Savitzky-Golay filter is applied to the “hepos” segment to get the corresponding eye velocity (“hevel”) segment.  
    3. A saccade detection algorithm is applied to the “hevel” segment which outputs a mask that provides the locations of detected saccades and can be used to set those elements to NaN values prior to certain metric calculations that require it.  
    4. A sinusoidal fit is performed (using linear regression) on the “htvel”, “hhvel”, and (non-saccade elements) “hepos” segments which gives us estimates of the sinusoidal amplitude and phase of the signals in each segment. It also provides us, using one of the segments that corresponds to the stimulus of the block (either “hhvel” or “htvel”), with a means of determining the index when the first “positive” stimulus cycle of the block begins.  
    5. With this index, we can further break up our segments into a matrix of sub-segments that correspond to each stimulus cycle of the block.  
    6. The average cycle trace can then be derived from each segment’s set of sub-segments and can be used for visualization in output plots and/or figures.  
12. Various metrics for each block are calculated and compiled into a data table (e.g. start/end time of the block, estimated VOR gain, estimated sinusoidal eye/chair/drum velocity amplitude and phase, etc.) and then saved as an Excel XLSX file in the experiment folder. Various plots and figures related to the analysis (that depend on which the researcher selects in the GUI) are also saved in the experiment folder.

 After running the experiment analysis MATLAB application, the example experiment folder should contain the following additional files:

* Two additional MAT files that contain various information used during the experiment analysis and generated upon its completion.  
* An XLSX file containing the calculated block-by-block analysis results.  
* Four or more MATLAB FIG figure files of the results from the various analyses that were performed.  
* Four or more PDF files that are simply the PDF versions of the same MATLAB figures above.

Key issue that needs to be addressed regarding our calibration analysis:

* Accuracy of the results depend on the initial parameters provided on the GUI prior to pressing the “GO” button (e.g. low-pass filter cutoff, Savitzky-Golay window size, saccade detection algorithm threshold, etc.). We need a robust and efficient application that can either find the optimal parameters itself or provide realtime, interactive visual feedback of how changing the parameters affects the downstream results.  
* This analysis also results in the generation of multiple additional files that become mixed in with the raw experiment data.  
* This GUI is also developed using MATLAB’s App Designer tool which saves the application as a MLAPP file. This file type cannot be searched, read, or opened in any IDE (e.g. Visual Studio Code) which makes version control between commits to our Github repository very difficult. Ideally, this application should instead be developed in Python, or at the very least, using a simple MATLAB “.m” script.

# Slice Physiology Experiments

Our lab also conducts slice physiology experiments (that are often paired with behavioral experiments, but not always) that involve patch clamp recordings of either Purkinje cells or granule cells in cerebellar brain slices using the pClamp 11 software suite provided by the company Molecular Devices. Each recording of an experiment is facilitated by an electrophysiology protocol file that defines the duration of the recording, the number of “sweeps” that are performed, the number of stimulations that are provided during each sweep, etc. Since we only conduct slice physiology once per mouse, it makes more sense to group patch clamp recordings by mouse (or “subject”). Describing a typical set of patch clamp recordings for any given mouse is very difficult, as they can vary greatly (even for mice within the same project, cohort, condition, etc.). For example:

* Depending on how well the surgery goes, we may be able to extract 1 to 3 “good” slices from any given mouse.  
* From these “good” slices, we can typically collect a set of patch clamp recordings from 1 to 3 cells per slice.  
* The number of recordings and which electrophysiology protocols are used for each cell of each slice can depend on a large number of factors such as the project, the experiment, the mouse, the quality of the slices, the location of the cell in the cerebellum and/or slice, the quality of the hardware/electrode setup, etc.

Every patch clamp recording is saved as an ABF file and its metadata will contain the file name of the electrophysiology protocol that was used to facilitate the recording. This means that the set of all ABF files that correspond to a particular mouse/subject can be grouped together (into sub-folders) by some combination of the cerebellar lobule and/or cell number. However, the file and folder structure of ABF files for a particular mouse/subject tends to vary between researchers, as well as between projects by the same researcher.

Since the electrophysiology protocols that were used within a set of ABF files can vary greatly, researchers developed many different custom analysis scripts in MATLAB and Python for each different use case. Each of these analysis scripts generate various new files related to the analysis in different locations of the project/experiment directory.

Key issues that needs to be addressed regarding our slice physiology experiments:

* The file and folder structure for slice physiology recordings of a mouse can differ greatly from mouse-to-mouse, making the data a nightmare in terms of data provenance. We need to devise/develop a method of consolidating sets of ABF files of mice into an effective data standard that utilizes the NWB file format and is compatible with BIDS.

# Data Storage, Management, Backup, and Sharing (as of January 2026\)

Our lab has a Google Workspace Enterprise (GWE) account where I have created a shared drive for each lab member to save their collected data. Every computer in the lab (all are Windows desktop PCs) that is used to collect/record data has the Google Drive desktop application installed on it and the researcher’s Google Drive shared drive virtually mounted. This means each researcher can collect data for their experiments and save it directly to their GWE shared drive. If a researcher would like to share their data with someone else, this will typically involve providing that person with access to that folder (or those folders) in their Google Shared drive, then that person can create a copy of the data in their own GWE shared drive folder.

Key issues that needs to be addressed regarding our data storage and management:

* Our researchers will typically have their own file and folder structure for their projects, which makes data provenance impossible and data sharing a nightmare. We need to develop a lab-wide data standard that can apply to any project, experiment, and dataset. Then, we can either force all our researchers to adhere to this data standard, or develop a robust software tool that the researchers can use that automates the restructuring of their experiment files and folders into the proper structures and formats.  
* Sharing data involves creating duplicate datasets throughout our GWE share drives. A better system might involve creating a dedicated GWE share drive for sharing datasets to reduce the need for duplicating.  
* Currently we are relying on the GWE system for ensuring our datasets uploaded to our GWE shared drives are safe and secure. With some researchers, there may be a local copy of their collected data on their computer hard drive, but there also might not be. We currently do not have a system for creating another backup of our dataset. A dedicated GWE shared drive for those datasets might be a solution for this.  
* Our current data management and sharing system also does not protect us from the potential possibility of a lab member intentionally seeking to sabotage a project and deleting valuable data from their GWE share drive. GWE does provide snapshots of individual files for some period of time, however I don’t think we can rely on this to protect our data. We need a system and/or software tool that backs up important data (e.g. data that was used for a published paper, conference presentation, etc.) to a dedicated GWE share drive that has restricted access (only certain designated administrators of the data can modify or delete data).

# Computers, Operating Systems, and the “Stanford” Ethernet/WiFi Network

* Our lab and all of our behavioral and slice physiology experiment rigs are located on the 2nd floor of the Sherman Fairchild Science Building on the Stanford University campus.  
* All of our behavioral experimental rigs have a dedicated Dell Precision 5820 Workstation PC (running Windows 11\) that interfaces with the USB 2.0 cameras used for calibration and the Power1401 CED Power1401 interface that is used to run and record all experiments.  
* All of our slice physiology experimental rigs also have a dedicated Dell Precision or Optiplex Workstation PC (running Windows 11\) that interfaces with Molecular Devices and/or Scientifica hardware to facilitate and record their experiments.  
* On the same floor we have two designated office rooms where each lab member is assigned their own Dell Precision/Optiplex Workstation PCs (running Windows 11).  
* All of the lab’s Dell Workstation PCs are connected to the Stanford network via a wired (ethernet) connection.  
* Some lab members use a laptop (running either Windows 10/11 or MacOS) to do some of their work, which connects to the Stanford network via a wireless (WiFi) connection.  
* Analysis of their data/experiments recorded on the various rig workstation PCs can be performed on the rig workstation PC, their office workstation PC, or their laptop.

Key limitation of all software development projects:

* Lab members have very limited to zero programming, command-line interface (CLI), and/or terminal experience, so all developed software and/or tools will typically need to have a GUI/UI front-end for easy use.  
* The entire codebase is developed, updated, and maintained by a single developer.