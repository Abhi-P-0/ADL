import time
import threading
import tkinter as tk
import cv2
import numpy as np
import pyautogui
import sv_ttk
import subprocess
from PIL import Image, ImageTk, ImageGrab
from tkinter import ttk, scrolledtext


class ADLGUI:

    ScreenShotPath = "./screenshot.png"
    ButtonPath = "./buttonImage.png"
    
    def __init__(self, title, height, width):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(0, 0)
        
        self.running = False

        self.SetupUI(height, width)
        
        self.root.mainloop()


    def MainButton(self):
        if (self.mainButtonText.get() == "START" and self.intervalInput.get() != ''):
            self.mainButtonText.set("STOP")

            self.running = True
            self.SendStatusMessage("Program started.")
            
            # Start screenshot update thread
            self.screenshotThread = threading.Thread(target=self.MainFunction, args=(int(self.intervalInput.get()),))
            self.screenshotThread.daemon = True
            self.screenshotThread.start()

        else:
            self.mainButtonText.set("START")

            self.running = False
            self.SendStatusMessage("Program stopped.")


    def MainFunction(self, interval):
        while (self.running):
            ss = self.TakeScreenshot()

            self.UpdateImage(ss)

            buttonCenter = self.FindButton(ss)

            if buttonCenter:
                self.SendStatusMessage(f"Button found at position: {buttonCenter}.")
                
                self.ClickButton(buttonCenter, False, 2)

            else:
                self.SendStatusMessage("Button not found.")
                
            time.sleep(interval)


    def UpdateImage(self, ss):       
        # Convert the screenshot to PhotoImage and update the label
        screenshot = Image.fromarray(cv2.cvtColor(ss, cv2.COLOR_BGR2RGB))

        resizedImage = self.ImageResize(screenshot, 854, 480)

        # Use method to safely update screenshot in GUI from thread
        self.root.after(0, self.UpdateImageDisplay, resizedImage)


    def UpdateImageDisplay(self, image):
        self.screenshotPhoto = ImageTk.PhotoImage(image)
        self.screenshotLable.configure(image=self.screenshotPhoto)


    def CreateNewButtonImage(self):
        # Ensure main funciton is off
        if (self.running):
            self.MainButton() 

        self.SendStatusMessage("Creating new image of button to look for.")

        self.root.iconify()

        subprocess.call([r'C:\\Windows\System32\SnippingTool.exe', '/clip'])

        self.root.after(1000, self.ProcessNewButtonImage)

        self.root.deiconify()

    
    def ProcessNewButtonImage(self):
        image = self.GetImageFromClipboard()

        if image:
            try:
                image.save(self.ButtonPath)
                
                resizedImage = self.ImageResize(image, 144, 144)
                
                # Update the photo image reference
                self.clickImagePhoto = ImageTk.PhotoImage(resizedImage)

                # Update the label
                self.clickImageLable.configure(image=self.clickImagePhoto)

                self.SendStatusMessage("Successfully created new button image.")
                
            except Exception as e:
                self.SendStatusMessage(f"Error processing new button image: {e}")
        
        else:
            self.SendStatusMessage("Something went wrong with grabbing the image from your clipboard, try again.")

    
    def GetImageFromClipboard(self):
        try:
            image = ImageGrab.grabclipboard()

            return image            
            
        except Exception as e:
            self.SendStatusMessage(f"Failed to get image from clipboard.")
            
        return None

        
    def TakeScreenshot(self):
        # screenWidth = self.root.winfo_screenwidth()
        # screenHeight = self.root.winfo_screenheight()

        # screenshot = pyautogui.screenshot(region=(0, 0, screenWidth, screenHeight))
        screenshot = ImageGrab.grab()
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        return screenshot
    

    def FindButton(self, screenshot, threshold=0.8):
        template = cv2.imread(self.ButtonPath, 0)

        grayScreenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(grayScreenshot, template, cv2.TM_CCOEFF_NORMED)

        _, maxVal, _, maxLoc = cv2.minMaxLoc(result)
        
        if maxVal >= threshold:
            topLeft = maxLoc
            h, w = template.shape

            center = (topLeft[0] + w // 2, topLeft[1] + h // 2)

            return center
        
        else:
            return None

    def ClickButton(self, position, moveOutOfWay, mouseSpeed=1):
        pyautogui.moveTo(position[0], position[1], duration=mouseSpeed)
        
        pyautogui.click()

        if (moveOutOfWay):
            pyautogui.moveTo(position[0] + 200, position[1], duration=1)
    
    
    def ImageResize(self, image, desiredWidth, desiredHeight):
        # desiredWidth = 854
        # desiredHeight = 480
        
        ratio = min(desiredWidth/image.width, desiredHeight/image.height)
        
        newWidth = int(image.width * ratio)
        newHeight = int(image.height * ratio)
        
        resizedImage = image.resize((newWidth, newHeight), Image.Resampling.LANCZOS)
        
        return resizedImage
    
    
    def SetupUI(self, height, width):
        sv_ttk.set_theme("dark")

        # Create window in the middle of the screen
        screenWidth = self.root.winfo_screenwidth()
        screenHeight = self.root.winfo_screenheight()
        
        center_x = int(screenWidth / 2 - width / 2)
        center_y = int(screenHeight / 2 - height / 2)
        
        self.root.geometry(f'{width}x{height}+{center_x}+{center_y}')

        # Configure grid weights for responsive layout
        self.root.grid_columnconfigure(0, weight=3)  # Screenshot and status column
        self.root.grid_columnconfigure(1, weight=1)  # Control panel column
        
        # Configure row weights
        self.root.grid_rowconfigure(0, weight=3)  # Screenshot row
        self.root.grid_rowconfigure(1, weight=1)  # Status area row

        # Create main containers
        leftFrame = ttk.Frame(self.root, padding=20)
        rightFrame = ttk.Frame(self.root, padding=20)
        statusFrame = ttk.Frame(self.root, padding=(20, 5, 20, 20))  # Different padding for status area
        
        leftFrame.grid(row=0, column=0, sticky="nsew")
        rightFrame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        statusFrame.grid(row=1, column=0, sticky="nsew")

        # Left side - Screenshot display
        try:
            screenshotImage = Image.open(self.ScreenShotPath)
        
        except Exception as e: # Image file doesn't exist, create one
            # self.SendStatusMessage(e)
            ImageGrab.grab().save(self.ScreenShotPath)

            screenshotImage = Image.open(self.ScreenShotPath)

        resizedImage = self.ImageResize(screenshotImage, 854, 480)

        self.screenshotPhoto = ImageTk.PhotoImage(resizedImage)
        self.screenshotLable = tk.Label(leftFrame, image=self.screenshotPhoto)
        self.screenshotLable.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Status Area panel
        statusLabel = ttk.Label(statusFrame, text="Log:", anchor="w")
        statusLabel.pack(fill="x", padx=5, pady=(0, 5))
        
        self.statusArea = scrolledtext.ScrolledText(
            statusFrame,
            height=8,  # Approximately 8 lines of text
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        self.statusArea.pack(fill="both", expand=True)
        self.statusArea.configure(state='disabled')  # Make it read-only

        # Right side - Control panel
        # Target image display
        try:
            clickImage = Image.open(self.ButtonPath)

        except Exception as e: # Image file doesn't exist, create one
            # self.SendStatusMessage(e)
            ImageGrab.grab().save(self.ButtonPath)

            clickImage = Image.open(self.ButtonPath)
        

        self.clickImagePhoto = ImageTk.PhotoImage(self.ImageResize(clickImage, 144, 144))
        self.clickImageLable = tk.Label(rightFrame, image=self.clickImagePhoto)
        self.clickImageLable.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # New button image control
        self.newButtonImageFrame = ttk.Frame(rightFrame, padding=10)
        self.newButtonImageFrame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.temp = tk.StringVar()
        self.temp.set("Look for new Button")
        self.newButtonImage = ttk.Button(self.newButtonImageFrame, textvariable=self.temp, command=self.CreateNewButtonImage)
        self.newButtonImage.pack(fill="x")

        # Interval control
        intervalFrame = ttk.Frame(rightFrame, padding=10)
        intervalFrame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(intervalFrame, text="Interval (seconds):").pack(side="left", padx=5)
        self.intervalInput = ttk.Spinbox(intervalFrame, from_=3, to=1000, width=5, increment=1, state='readonly')
        self.intervalInput.pack(side="left", padx=5)

        # Main control button (START/STOP button)
        self.mainButtonFrame = ttk.Frame(rightFrame, padding=10)
        self.mainButtonFrame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.mainButtonText = tk.StringVar()
        self.mainButtonText.set("START")
        self.mainButton = ttk.Button(self.mainButtonFrame, textvariable=self.mainButtonText, command=self.MainButton)
        self.mainButton.pack(fill="x")

        
    def SendStatusMessage(self, message):
        timestamp = time.strftime('%H:%M:%S')
        self.statusArea.configure(state='normal')

        self.statusArea.insert('end', f'[{timestamp}] {message}\n')

        self.statusArea.see('end')  # Auto-scroll to bottom
        self.statusArea.configure(state='disabled')


# def main():
app = ADLGUI("Auto Downloader", 720, 1280)

# if __name__ == "__main__":
#     main()