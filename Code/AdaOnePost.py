"""

File: KUKA Welding Program Converter
Description: This application is designed to convert WAAM (Wire Arc Additive Manufacturing) paths generated by AdaOne software into KUKA 
             welding programs compatible with the Arc Tech Basic (ATB) technology package. The app translates the additive manufacturing 
             toolpaths into optimized welding instructions, enabling seamless integration with KUKA robotic systems for precise and 
             efficient welding operations.
Author: David Pareira
Date: 28/08/2024
Version: 0.2
Dependencies: The code generated is Valid for ATB compatible with KSS 8.6
Usage Instructions: Run the Code and specify the input path, output path and job number which you wish you use for welding program. 

"""

import os
import tkinter as tk 
import sys
import shutil

class file_conversion():

    def __init__(self):
        self.layer_list = []
        self.mainFileName = ''

    def read_file(self,path,fileToRead_src):
        """read the files and store the date in read lines array"""
        
        file2read_src = open(path+'\\'+fileToRead_src+'.src','r')
        self.read_lines = []
        
        for array,line in enumerate(file2read_src):
            self.read_lines.append(line)
            
    def write_file(self,path,fileNameToWrite): 
        """It detects ;process_on markers to initiate the ARCON command and ;process_off markers for the ARCOFF command. All lines between these markers are converted into ARCSWI instructions. Identifies changes in velocity within the welding program and generates specific weld data entries in the .DAT file accordingly."""

        fileToWrite_src = open(path+"\\"+fileNameToWrite+".src","w+")
        fileToWrite_dat = open(path+"\\"+fileNameToWrite+".dat","w+")
        newFile = True

        #write default content in dat file 
        fileToWrite_dat.write("&ACCESS RV \n")
        fileToWrite_dat.write(f"DEFDAT {fileNameToWrite}\n")
        fileToWrite_dat.write(";FOLD EXTERNAL DECLARATIONS;%{PE}%MKUKATPBASIS,%CEXT,%VCOMMON,%P\n"
                              ";FOLD BASISTECH EXT;%{PE}%MKUKATPBASIS,%CEXT,%VEXT,%P\n"
                              "EXT  BAS (BAS_COMMAND  :IN,REAL  :IN )\n"
                              "DECL INT SUCCESS\n"
                              ";ENDFOLD (BASISTECH EXT)\n"
                              ";FOLD USER EXT;%{E}%MKUKATPUSER,%CEXT,%VEXT,%P\n"
                              ";Make your modifications here\n"
                              ";ENDFOLD (USER EXT)\n"
                              ";ENDFOLD (EXTERNAL DECLARATIONS)\n")
        fileToWrite_dat.write("\n")
        fileToWrite_dat.write('DECL stArcDat_T WP1={WdatId[] "WP1",Info {Version 304021224},Strike {SeamName[] " ",PartName[] " ",SeamNumber 0,PartNumber 0,DesiredLength 0.0,LengthTolNeg 0.0,LengthTolPos 0.0,LengthCtrlActive FALSE}} \n')
        
        wdati = 1
        jobNumber = str(self.weldingJobNumber)
        

        for i in range (0 , len(self.read_lines)):
            newline = self.read_lines[i]
            

            if newline.strip().lower() == ";process_on" :
                self.process_ON = True
                self.arc_on = True
                self.arc_off = False
                self.arc_swi = False

            if newline.strip().lower() == ";process_off" :
                self.process_ON  =False

            if (("$VEL.CP" in newline and self.process_ON) or ( self.arc_swi and newFile )) :
                newFile = False
                param = ("wdat"+str(wdati)).upper()
                wdati  = wdati + 1
                if "$VEL.CP" in newline :
                    var,value = newline.split("=")
                    self.value1 = str(value).strip()
                #create a weld data 
                fileToWrite_dat.write('DECL stArcDat_T '+param+'={WdatId[] ''"' +param+'"'', Strike'+str(self.process_ON)+' {JobModeId[] "Job mode",StartTime 0.0,PreFlowTime 0.0,Channel1 0.0,Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,PurgeTime 0.0},Weld {JobModeId[] "Job mode",ParamSetId[] "Set1",Velocity '+self.value1+',Channel1 '+jobNumber+',Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0},Weave {Pattern #None,Length 4.00000,Amplitude 2.00000,Angle 0.0,LeftSideDelay 0.0,RightSideDelay 0.0},Crater {JobModeId[] "Job mode",ParamSetId[] "Set2",CraterTime 0.0,PostflowTime 0.0,Channel1 '+self.value1+',Channel2 0.0,Channel3 0.0,Channel4 0.0,Channel5 0.0,Channel6 0.0,Channel7 0.0,Channel8 0.0,BurnBackTime 0.0}}\n')
            
            if "LIN" in newline:
                if  self.arc_on:
                    fileToWrite_src.write(f"TRIGGER WHEN DISTANCE = 1 DELAY = ArcGetDelay(#PreDefinition,{param}) DO ArcMainNG(#PreDefinition, {param}, WP1) PRIO = -1 \n")
                    fileToWrite_src.write(f"TRIGGER WHEN PATH = ArcGetPath(#OnTheFlyArcOn, {param}) DELAY = ArcGetDelay(#GasPreflow, {param}) DO ArcMainNG(#GasPreflow, {param}, WP1) PRIO = -1 \n")
                    fileToWrite_src.write(f"TRIGGER WHEN PATH = ArcGetPath(#OnTheFlyArcOn, {param}) DELAY = 0 DO ArcMainNG(#ArcOnMoveStd, {param}, WP1) PRIO = -1 \n")
                    fileToWrite_src.write(f"ArcMainNG(#ArcOnBeforeMoveStd, {param}, WP1)\n")
                    fileToWrite_src.write(newline)  
                    fileToWrite_src.write(f"ArcMainNG(#ArcOnAfterMoveStd, {param}, WP1)\n")
                    fileToWrite_src.write("\n")
                    self.arc_on = False
                    self.arc_swi = True

                elif self.arc_swi and self.read_lines[i+1].strip().lower()!= ";process_off":
                    fileToWrite_src.write(f"TRIGGER WHEN DISTANCE = 1 DELAY = 0 DO ArcMainNG(#ArcSwiMoveStd, {param}, WP1) PRIO = -1\n")
                    fileToWrite_src.write(f"ArcMainNG(#ArcSwiBeforeMoveStd, {param}, WP1)\n")
                    fileToWrite_src.write(newline)
                    fileToWrite_src.write(f"ArcMainNG(#ArcSwiAfterMoveStd, {param}, WP1)\n")
                    fileToWrite_src.write("\n")
                    

                elif self.read_lines[i+1].strip().lower() == ";process_off":
                    fileToWrite_src.write(f"TRIGGER WHEN PATH = ArcGetPath(#ArcOffBefore, {param}) DELAY = 0 DO ArcMainNG(#ArcOffBeforeOffStd, {param}, WP1) PRIO = -1 \n")
                    fileToWrite_src.write(f"TRIGGER WHEN PATH = ArcGetPath(#OnTheFlyArcOff, {param}) DELAY = 0 DO ArcMainNG(#ArcOffMoveStd, {param}, WP1) PRIO = -1 \n")
                    fileToWrite_src.write(f"ArcMainNG(#ArcOffBeforeMoveStd, {param}, WP1)\n")
                    fileToWrite_src.write(newline)
                    fileToWrite_src.write(f"ArcMainNG(#ArcOffAfterMoveStd, {param}, WP1)\n")
                    fileToWrite_src.write("\n")
                    self.arc_swi = False
                    self.arc_on = False
                    self.arc_off = False
                    self.process_ON = False
               
                else:
                    fileToWrite_src.write(newline)
            else:
                fileToWrite_src.write(newline)
            if newline.strip()=="END":
                fileToWrite_dat.write("\n")
                fileToWrite_dat.write("ENDDAT")
                break

    def list_Files(self,pathSource):
        """List the files inside the folder and store it in a list """
        path = pathSource
        try:
            self.files= os.listdir(path)
        except:
            print("Invalid folder location")

        self.check_files(self.files)
        
        self.mainFileName,ext = self.files[0].split(".")
        self.totalLayers = int((len(self.files)-2)/2)

        if not self.CFinvalid :
            for ll in self.files[3::2]:
                name,ext = ll.split(".")
                self.layer_list.append(name)
        
    def check_files(self,files):
        """Checks if the folder path given contains valid files  i.e .src and .dat files"""
        self.CFinvalid = False
        for self.cf in files[1:int((len(self.files)))]: 
            if ".src" in self.cf or ".dat" in self.cf:
                pass
            else:
                self.CFinvalid = True
                print("invalid")
                self.panel_output("Input path does not contain valid files")
                break

    def check_output_files(self,ippath,oppath):

        if len(os.listdir(ippath)) == len(os.listdir(oppath)):
            self.panel_output("Conversion Successfull")
        else:
            self.panel_output("No of Input files does not match Converted file number, create empty output folder")
         
    def panel_output(self,panelmsg):
        msgonPanel = "Note :" + panelmsg
        self.entryPanel.config(text=msgonPanel)

    def start_conversion(self):
        inputPath = self.entryInputDirectory.get()
        outputPath = self.entryOuputDirectory.get()
        self.weldingJobNumber = self.wJobNumber.get()


        if inputPath != outputPath :

            panelMsg1 = ''
            panelMsg2 = ''
            panelMsg3 = ''
            jobValid = True


            if not os.path.exists(inputPath) :
                panelMsg1 = "Invalid Source Path; "
            
            if not os.path.exists(outputPath) :
                panelMsg2 = "Invalid Target Path; "
            
            try:
                if not self.weldingJobNumber or int(self.weldingJobNumber)<=0 or int(self.weldingJobNumber)>999 or (self.weldingJobNumber.isdigit()==False):
                    jobValid = False
                    panelMsg3 = "Invalid Job Number"
            except:
                panelMsg3 = "Invalid Job Number"
                jobValid = False

                
            panelmsg = panelMsg1+panelMsg2+panelMsg3
            self.panel_output(panelmsg)


            if os.path.exists(inputPath) and os.path.exists(outputPath) and jobValid :
                
                self.list_Files(inputPath)
                
                if not(self.CFinvalid): 
                    #copy main files
                    main_path_input = inputPath+'\\'+self.mainFileName
                    main_path_output = outputPath+'\\'+self.mainFileName
                    shutil.copyfile(main_path_input+'.src',main_path_output+'.src')
                    shutil.copyfile(main_path_input+'.dat',main_path_output+'.dat')

                    self.arc_on = False
                    self.arc_swi = False
                    self.arc_off = False
                    self.process_ON = False
                    self.value1 = ''

                    for i in self.layer_list:
                        self.read_file(inputPath,i)
                        self.write_file(outputPath,i)

                    self.check_output_files(inputPath,outputPath)

                    self.layer_list = []
        
        else:
            self.panel_output("Source path and Target path cannot be same")
        
    def resource_path(self,relative_path):
        """ Get the absolute path to the resource, works for development and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def gui_parameter(self):
    
        #Make your modification here to do any chnages in the GUI 

        gui = tk.Tk(className="AdaOne Program Converter",)
        gui.minsize(width=600,height=600)
        gui.maxsize(width=600,height=600)
        icoImg = self.resource_path("code\\asset\\logo.ico")
        gui.iconbitmap(icoImg)
        imgpath = self.resource_path("code\\asset\\bg.png")
        bgImg = tk.PhotoImage(file =imgpath)

        tk.Label(gui,image = bgImg ).pack()

        tk.Label(gui,text="Ver. 0.2",bg="white",height=2,width=9).place(x= 540,y=-10)

        tk.Label(gui,text="Enter Source Directory",bg="white",).place(x= 0,y=30)
        self.entryInputDirectory = tk.Entry(gui,border=2)
        self.entryInputDirectory.place(x = 150, y=30,width=300,height=20)

        tk.Label(gui,text="Enter Target Directory",bg="white",).place(x= 0,y=70)
        self.entryOuputDirectory = tk.Entry(border=2)
        self.entryOuputDirectory.place(x = 150, y=70,width=300,height=20)

        tk.Label(gui,text="Welding Job Number",bg="white",).place(x= 0,y=110)
        self.wJobNumber= tk.Entry(border=2)
        self.wJobNumber.place(x = 150, y=110,width=50,height=20)

        tk.Button(gui,text="Convert",command=self.start_conversion,height=7,width=10).place(x=475,y=20)

        self.entryPanel = tk.Label(gui,border=2,anchor='w')
        self.entryPanel.place(x=10, y= 150,width= 580,height=50)
        gui.mainloop()
        

if __name__ == '__main__':
    fc = file_conversion()
    gui_param = fc.gui_parameter()

    
