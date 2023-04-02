# BigTree3DPlugin Suit
BigTree3D G-code for model previews
<p align="center"><img src="BigTree3DPlugin\DCIM_0.png" width="95%"></p>

# Requirements

- Cura version: `5.2`
- Operating system: Windows, Linux, MacOS
- Hardware supported: All versions of touch screen hardware released by BIGTREETECH support this feature as long as the firmware is updated, including 
 TFT24, TFT28, TFT35, TFT43, TFT50, TFT70...
- TFT Firmware: `Vx.x.27`

# How to Install the plugin

1. Download [This repository](./archive/master.zip), then unzip.

2. Find your Cura plugins directory:
   ## Windows
   The default installation path is `C:\Program Files\Ultimaker Cura {VERSION}\plugins`.
   ## macOS
   The default installation path is `~/Library/Application Support/cura/{VERSION}/plugins`
   ## Linux
   The default installation path is `~/.local/share/cura/{VERSION}/plugins`.

3. Copy the following folders to the __Cura plugins__ folder you located in Step 2
   - `BigTree3DPlugin`, 
   - `BigTreeExtension`, 
   - `BigTreeRemovableDriveOutputDevice`

   ![img](BigTree3DPlugin\DCIM_1.png)

4. Open the STL model in Cura and click `Slice`.

5. Click the small up arrow on the right and select `Save as BigTree3D format`:
   ![img](BigTree3DPlugin\DCIM_2.png)

6. Model preview is now available:
   ![](BigTree3DPlugin\DCIM_3.png)
   ![](BigTree3DPlugin\DCIM_4.png)
    


# Enable in your printer

1. Update touch screen firmware to a version after [this Pull Request](https://github.com/bigtreetech/BIGTREETECH-TouchScreenFirmware/pull/844).  
The first release to include this feature will be `Vx.x.27`.

2. Enable model previews by disabling **List Mode** under:  
  `Menu` → `Settings` → `Feature` → `Files viewer List Mode`.

