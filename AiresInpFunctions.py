
import os
import sys
import numpy as np
import random
#import matplotlib.pyplot as plt #in lyon you dont need to plot (and it will crash cos it cannot open the display
#from mpl_toolkits.mplot3d import Axes3D #
#other, nore elegant solution:
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt



#This function generates the star shape positions for antennas on a slope, or on flat ground

#Caveats: 1) You can have negative altitude antennas in the input, as long as the local altitude of the antena keeps being positive.
# The index of refraction model will break if altitude is negative. So be carefull if you are going for inclined planes. There is a way to keep the pattern contained in the slope
# see the code for hints on how to do this

def CreateAiresStarShapeInp(zenith, azimuth, alpha, az_slope, cone_vertex=100000.0, cone_ang=2.0, nant=20, az_B=0.0, zen_B=147.4, outputfile="TestInput.inp", outmode="a", RandomFraction = 0, stepmode="linear"):

  #==============================================================================
  #Original version from A. Zilles, extensivly modified by M. Tueros in Oct 2019

  #Zenith[deg, AIRES,deg]:
  #Azimuth[deg, AIRES,deg]:
  #Alpha: slope of the ground
  #az_Slope: azimuth of the slope. If az_slope=azimuth, the slope is facing perpendicular to the the shower
  #cone_vertex (dist_fromxmax) [m]: Ditance from the core to the vertex of the cone defining the starshape pattern (it should be xmax, or before xmax, to make sense).
  #cone_ang (max_ang) [deg]: Aperture of the cone of the starshape patern. (2 deg)
  #nant= number of antennas per arm, 8 arms (so you end with nant*8). Antennas will be equally spaced along the arm.
  #az_B: Azimuth of the magnetic field, to get the vxB components. Usually 0 if azimuth 0 points north (Aires Magnetic coordinates).
  #zen_B: Zenith of the magnetic field. 147,43 deg in Lenghu (152.95 deg in ullastay??), Direction where we point to (incl +90)
  #outputfile: path and name of the outputfile (generally ending in .inp)
  #outmode:a for append, w to overwrite (it seems that it always append...)
  #RandomFraction: If you want to add a fraction of antenas spaced randomly (but uniformly random)
  #stepmode: 2 stepping modes are implemented: "linear" will go from 0 (not included) to cone_ang (included) in steps of cone_ang/nant
  #                                            "quadratic" will go from 0 (not included) to cone_ang (included) in cuadratic steps, with an offset

  # Here (x,y,z) = (Northing,Westing, Up). Alt ref at sea level.
  # Use Zhaires (theta, phi) convention: defined wrt direction of origin
  # inside Zhaires a conversion to zaxis down is made
    degtorad= np.pi/180.
    radtodeg= 180./np.pi

    DISPLAY = 0
    PRINT = 1

    # mountain slope
    alpha = float(alpha)*degtorad

    ## Angles: ATTENTION use ZHAireS angle convention
    zen2=float(zenith)*degtorad
    az2=float(azimuth)*degtorad

    zen_rad=zen2
    az_rad=az2

    #Since the shower core is always on 0,0,ground and this gives negative antenna heights (which are disliked by coreas), you might want to "move" the slope until it intesects the shower axis
    #high enough so that you dont have negative antennas. Note however, that this will make the distance to xmax shorter by an amount that depends on the geometry. This might or not
    #be important acording to your needs. Here is a model that uses a fixed refraction index that estimates the cherenkov cone width, and moves the intersection so that the cherenkov
    #cone is always on a positive height antenna. But you could also hard code a fixed height, or a fixed angle (i.e, make the angle equal to the cone angle)
    #for kumiko study i will fix it to 0, so that the antenna pattern is centered at 0,0,ground
    # translation , c includes already (0,0,h)

    theta_ch=0 #set to 0 to have all antenna patterns centered in the origin (h will be 0)
    #theta_ch=cone_ang*degtorad #theta ch controls the widht of the cone used to compute the height of the center of the cone., in order to intercept the mountain plane before
    #n_ref=1.0003 # usually depends on density at Xmax, here neglected
    #theta_ch=np.arccos(1./n_ref)
    y= -cone_vertex * np.sin(theta_ch)*np.cos(zen_rad-alpha+theta_ch)/( (np.sin(zen_rad-alpha))**2. -(np.cos(theta_ch))**2.  ) # major axis od ellipse
    h= np.sin(alpha) *y # height of antenna array center on the mountain, if complete shower should be on the mountain




    ### Create star shape in GRAND coordinates
    # Direction where Earth mag field points to
    az_B = az_B*degtorad  # North = Magnetic North
    zen_B = zen_B*degtorad #Direction where we point to
    B = np.array([np.cos(az_B)*np.sin(zen_B),np.sin(az_B)*np.sin(zen_B),np.cos(zen_B)]) #in LOFAR coordinates

    v = np.array([np.cos(az_rad)*np.sin(zen_rad),np.sin(az_rad)*np.sin(zen_rad),np.cos(zen_rad)])
    v = v/np.linalg.norm(v)
    vxB = np.array([v[1]*B[2]-v[2]*B[1],v[2]*B[0]-v[0]*B[2],v[0]*B[1]-v[1]*B[0]])
    vxB = vxB/np.linalg.norm(vxB)
    vxvxB = np.array([v[1]*vxB[2]-v[2]*vxB[1],v[2]*vxB[0]-v[0]*vxB[2],v[0]*vxB[1]-v[1]*vxB[0]])
    vxvxB = vxvxB/np.linalg.norm(vxvxB)


    ## in principle, antenna array center should be at a fixed height on a slanted surface,
    ## just the star shape pattern should be orientated with the shower direction
    ####### projection on mountain

    # define mountain slope as plane which is always facing the shower
    az_mount=np.deg2rad(az_slope)
    u=np.array([np.cos(az_mount+0.5*np.pi), np.sin(az_mount+0.5*np.pi),0.]) # always z=0, vector should be perp to shower axis = az_mount +0.5*pi
    v=np.array([np.sin(0.5*np.pi-alpha)*np.cos(az_mount+np.pi), np.sin(0.5*np.pi-alpha)*np.sin(az_mount+np.pi), np.cos(0.5*np.pi-alpha) ]) # describes the mountain slope and should be perp to u,0.5*np.pi-alpha to account for mountain slope, az_mount+np.pi because slope pointing towards inverse dir of shower
    n=np.cross(u,v)

    #NOTE: z component of alpha flipped
    a =np.array([np.sin(zen_rad)*np.cos(az_rad), np.sin(zen_rad)*np.sin(az_rad), np.cos(zen_rad)]) # shower direction
    #print(a,zen_rad,az_rad,"first!")
    a=a/mag(a)
    a_op = np.array([a[0], a[1],0]) #ortogonal projection on ground to shift for shower axis
    #print(a_op,"second!")
    if(mag(a_op)!=0):
      a_op=a_op/mag(a_op)

    d= h* np.tan(zen_rad)# shift length to respect shower axis

    r0= np.array([0,0,h]) + d*a_op# +c* v #works like plane0, gives you the positions vector of the projection

    nrandom=int(nant*8*float(RandomFraction))

    #### star shape pattern in xyz
    xyz1=np.zeros([nant*8+nrandom,3])
    xyz=np.zeros([nant*8+nrandom,3])
    xyz2=np.zeros([nant*8+nrandom,3]) # back trafo in vxvxB

    max_ang = cone_ang*degtorad  # Most distant antenans are max_ang from axis
    linstep = cone_vertex*np.tan(max_ang)/nant
    if(stepmode=="linear" or stepmode=="Linear"):
      for i in np.arange(1,nant+1):   #AZ setup
        for j in np.arange(8):
          step= i*linstep
          xyz0 = step*(np.cos(float(j/4.0)*np.pi)*vxB+np.sin(float(j/4.0)*np.pi)*vxvxB) # pattern in xyz     xyz0 # z*v=0, since z=0
          xyz1[(i-1)*8+j]=xyz0 # original starshape produced

          # intersection of shower and mountain plane
          b=-np.dot(n,xyz1[(i-1)*8+j])/ np.dot(n, a)
          xyz[(i-1)*8+j]= xyz1[(i-1)*8+j] +b*a +r0 # projected


    cuadofset = 0.15 #it was 0.25 the first time we used it, but i want more antensas inside the cone. this requires max_ang to be more than 0.04...its small enough for all practical aplications
    cuadstep = (np.sqrt(cone_ang)-cuadofset)/nant


    if(stepmode=="quadratic" or stepmode=="Quadratic"):
      for i in np.arange(1,nant+1):   #AZ setup
        for j in np.arange(8):
          step = (i*cuadstep+cuadofset)*(i*cuadstep+cuadofset)
          #if(j==1):
          #  print(cone_vertex*np.tan(step*degtorad),cuadstep,i)
          xyz0 = cone_vertex*np.tan(step*degtorad)*(np.cos(float(j/4.0)*np.pi)*vxB+np.sin(float(j/4.0)*np.pi)*vxvxB) # pattern in xyz     xyz0 # z*v=0, since z=0
          xyz1[(i-1)*8+j]=xyz0 # original starshape produced

          # intersection of shower and mountain plane
          b=-np.dot(n,xyz1[(i-1)*8+j])/ np.dot(n, a)
          xyz[(i-1)*8+j]= xyz1[(i-1)*8+j] +b*a +r0 # projected

    ##set of random test points
    for i in np.arange(0,nrandom):

      randomd= linstep*nant*np.sqrt(float(random.uniform(0, 1))) #we use the square root to sample the area uniformly.
      randomangle= 2*np.pi*float(random.uniform(0, 1))

      xyz0 = randomd*(np.cos(randomangle)*vxB+np.sin(randomangle)*vxvxB) # pattern in xyz     xyz0 # z*v=0, since z=0
      xyz1[nant*8+i]=xyz0 # original starshape produced

      # intersection of shower and mountain plane
      b=-np.dot(n,xyz1[nant*8+i])/ np.dot(n, a)
      xyz[nant*8+i]= xyz1[nant*8+i] +b*a +r0 # projected


    if PRINT:
        print 'produce input file ....', outputfile

        file= open(outputfile, outmode)

        file.write('\n####################################################################################\n')
        file.write('# Starshape Pattern created with CreateAiresStarshapeInp.py v1.1\n')
        file.write('# mountain slope: {0:.2f} deg\n'.format(alpha*radtodeg))
        file.write('# mountain azimuth: {0:.2f} deg\n'.format(az_slope))
        file.write('# cone vertex distance: {0:.3f} Km\n'.format(cone_vertex/1000.0))
        file.write('# cone angle: {0:.2f} deg\n'.format(cone_ang))
        file.write('# Number of Antennas per ray: {0:d}\n'.format(nant))
        file.write('# Separation Mode: {0:s}\n'.format(stepmode))
        file.write('# Magnetic Field Zenith: {0:.2f} deg\n'.format(zen_B*radtodeg))
        file.write('# Magnetic Field Azimuth: {0:.2f} deg\n'.format(az_B*radtodeg))

        file.write('####################################################################################\n\n')
        file.write('ZHAireS On\n')
        file.write('FresnelTime On\n')
        for i in np.arange(nant*8):
            file.write("AddAntenna A{0:d} {1:11.2f} {2:11.2f} {3:11.2f}\n".format(int(i),xyz[i,0],xyz[i,1],xyz[i,2]))

        file.write('####################################################################################\n\n')
        if(nrandom>0):
          file.write('#{0:d} Crosscheck Antennas  ########################################################\n\n'.format(nrandom))
        for i in np.arange(nrandom):
            file.write("AddAntenna CrossCheckA{0:d} {1:11.2f} {2:11.2f} {3:11.2f}\n".format(int(nant*8+i),xyz[nant*8+i,0],xyz[nant*8+i,1],xyz[nant*8+i,2]))
        file.write('####################################################################################\n\n')

        file.close()

#    if DISPLAY:
#
#      for i in np.arange(nant*8):
#        xyz2[i]=GetUVW(xyz[i], r0[0], r0[1], r0[2], zen_rad, az_rad, az_B, zen_B)# as used later to fo in vxB
#
#
#      shower=np.zeros([200,3])
#      mount_u=np.zeros([200,3])
#      mount_v=np.zeros([200,3])
#      for i in np.arange(0,200):
#        shower[i]= (i-100)*100 *a +r0
#        mount_u[i]= (i-100)*100 *u +r0
#        mount_v[i]= (i-100)*100 *v +r0
#      fig1=plt.figure(1, figsize=(12, 10), dpi=120, facecolor='w', edgecolor='k')
#      title="zen_G="+str(zen_rad*radtodeg) + " az_G="+str(az_rad*radtodeg) + " slope=" +str(alpha*radtodeg)
#      fig1.suptitle(title, fontsize=16)
#
#      #plt.subplot(221)
#
#      #plt.scatter(xyz[:,0],xyz[:,1], c='red')
#      #plt.scatter(shower[:,0],shower[:,1], c='blue')
#
#      #plt.xlabel(r"x")
#      #plt.ylabel(r"y") #, fontsize=16
#      #plt.axis('equal')
#
#      #######
#      #plt.subplot(222)
#      #ax=plt.plot()
#
#      #plt.scatter(xyz[:,0],xyz[:,2], c='red', label="antennas")
#      #plt.scatter(shower[:,0],shower[:,2], c='blue', label="shower axis")
#      #plt.xlabel(r"x")
#      #plt.ylabel(r"z") #, fontsize=16
#      #plt.axis('equal')
#      #plt.plot([min(shower[:,0]), max(shower[:,0])], [h_ulas, h_ulas], 'k-', label="Ulastai height")
#      #plt.legend(loc='best')
#
#      #plt.show()
#
#      #######
#      #plt.subplot(121)
#      #ax=plt.plot()
#      #plt.scatter(xyz1[:,1],xyz1[:,2], c='green') # produce star shape pattern
#      #plt.scatter(xyz2[:,1],xyz2[:,2], c='yellow') # back transformed star shape pattern
###     plt.scatter(shower[:,1],shower[:,2], c='blue')
#      #plt.xlabel(r"vxB - back trafo ")
#      #plt.ylabel(r"vxvxB - back trafo") #, fontsize=16
#      #plt.axis('equal')
#      #######
#      #plt.subplot(122)
#      #ax = fig1.add_subplot(224, projection='3d')
#      plt.subplot(111)
#      ax = fig1.add_subplot(111, projection='3d')
#
#      ax.scatter(xyz1[:,0],xyz1[:,1],xyz1[:,2], c='green') # produced star shape
#      ax.scatter(xyz[:,0],xyz[:,1],xyz[:,2], c='red')  # projected
#      ax.scatter(shower[:,0],shower[:,1],shower[:,2], c='blue')  # shower
#      ax.scatter(mount_u[:,0],mount_u[:,1],mount_u[:,2], c='black')  # mountain
#      ax.scatter(mount_v[:,0],mount_v[:,1],mount_v[:,2], c='black')  # mountain
#      #ax.scatter(xyz3[:,0],xyz3[:,1],xyz3[:,2], c='yellow') # backtransformed
#
#      plt.axis('equal')
#      plt.xlabel(r"x ")
#      plt.ylabel(r"y") #, fontsize=16
#      #plt.zlabel(r"z") #, fontsize=16
#
#      plt.show()

def mag(x):
    y=0
    for i in range(0,len(x)):
        y=y+float(x[i])*float(x[i])
        #print i , float(x[i])*float(x[i]), y
    return float(np.sqrt(float(y)))


# NOTE: this functions returns other order of coordinates since the 3rd component should be zero in shower coordinates
def GetUVW(pos, cx, cy, cz, zen, az, phigeo, bfieldangle):

   relpos = pos-np.array([cx,cy,cz])
   inc=bfieldangle

   B = np.array([np.cos(phigeo)*np.sin(inc), np.sin(phigeo)*np.sin(inc),np.cos(inc)]) #from oliviers script including phigeo
   B=B/np.linalg.norm(B)
   v = np.array([np.cos(az)*np.sin(zen),np.sin(az)*np.sin(zen),np.cos(zen)]) # or *-1: change the direction
   v=v/np.linalg.norm(v)
   #print v
   vxB = np.cross(v,B) #np.array([v[1]*B[2]-v[2]*B[1],v[2]*B[0]-v[0]*B[2],v[0]*B[1]-v[1]*B[0]]) # crossproduct
   vxB = vxB/np.linalg.norm(vxB)
   vxvxB = np.cross(v,vxB) #np.array([v[1]*vxB[2]-v[2]*vxB[1],v[2]*vxB[0]-v[0]*vxB[2],v[0]*vxB[1]-v[1]*vxB[0]])# crossproduct
   vxvxB = vxvxB/np.linalg.norm(vxvxB)

   return np.array([np.dot(v,relpos),np.dot(vxB,relpos),np.dot(vxvxB,relpos)]).T # vector dot


def CreateAiresInputHeader(TaskName, Primary, Zenith, Azimuth, Energy, RandomSeed=0.0, OutputFile="TestInput.inp", OutMode="a" ):

#TaskName, the name of the task. All files in the run will have that name, and some extension. It is usually also the name of the .inp, but not necessarily
#Primary [AIRES]: Proton, Iron, Gamma, or see Aires Manual
#Zenith[deg, AIRES,deg]:
#Azimuth[deg, AIRES,deg]:
#Energy[EeV]
#RandomSeed. A number from [0 to 1). 0 is that the seed is generated automatically by the script. "Automatic", leaves the work of setting a random seed to Aires.
#output

  print 'produce input file header on:', OutputFile

  base=os.path.basename(OutputFile)

  file= open(OutputFile, OutMode)
  file.write('\n##############################################################################\n')
  file.write('# Aires simulation header generated with CreateAiresInputHeader                #\n')
  file.write('################################################################################\n')

  task='TaskName '+str(TaskName)+ '\n'
  file.write(task)
  prim='PrimaryParticle '+str(Primary) + '\n'
  file.write(prim)
  file.write('PrimaryEnergy {0:.5} EeV\n'.format(float(Energy)))
  file.write('PrimaryZenAngle {0:6.5} deg\n'.format(Zenith))
  file.write('PrimaryAzimAngle {0:.5} deg Magnetic\n'.format(Azimuth))
  if(RandomSeed==0.0):
    seed=random.uniform(0, 1)
  else:
    seed=float(RandomSeed)
  if(RandomSeed!="Automatic"):
    file.write('RandomSeed {0:1.9f}\n'.format(seed))
  file.write('################################################################################\n')
  file.close()

def CreateExampleSkeleton(OutputFile="TestInput.inp", OutMode="a"):

  print 'produce example Skeleton ....', OutputFile

  base=os.path.basename(OutputFile)

  file= open(OutputFile, OutMode)
  file.write('\n##############################################################################\n')
  file.write('# Aires simulation skeleton example, generated with CreateExampleSkeleton      #\n')
  file.write('################################################################################\n')
  file.write('#\n')
  file.write('\n#Configure the site\n')
  file.write('AddSite Lenghu 38.870398 deg 92.334037 deg 2900.00 m\n')
  file.write('Site Lenghu\n')
  file.write('GeomagneticField 54.021 uT 57.43 deg 0.72 deg\n')
  file.write('GroundAltitude 2900 m\n')
  file.write('\n#Set up thinning.\n')
  file.write('Thinning 1E-4 Rel\n')
  file.write('ThinningWFactor 0.06\n')
  file.write('\n#Table Export\n')
  file.write('Export 2001 O d\n')
  file.write('Export 2205 O d\n')
  file.write('Export 2207 O d\n')
  file.write('Export 1205 O a\n')
  file.write('Export 1207 O a\n')
  file.write('RLimsTables 100 m 3.5 km\n')
  file.write('\n#increase the number of observing levels (more detailed longitudinal files, at the expense of a bigger idf data file)\n')
  file.write('ObservingLevels 510 100.000 km 2.9 km\n')
  file.write('\n#dont save ground or lgtpcles if you wont use them (waste space)\n')
  file.write('SaveNotInFile lgtpcles All\n')
  file.write('SaveNotInFile grdpcles All\n')
  file.write('\n#AIRES Misc Section\n')
  file.write('PropagatePrimary On\n')
  file.write('TotalShowers 1\n')
  file.write('MaxCpuTimePerRun 120 min\n')
  file.write('\n#We make the Antenna time window tight to reduce output. Be sure to tune it for your needs.\n')
  file.write('(this will produce 513 time bins, of wich 512 will be in the file, to have a power of 2)\n')
  file.write('AntennaTimeMin -66 ns\n')
  file.write('AntennaTimeMax 960 ns\n')
  file.write('TimeDomainBin 2 ns\n')
  file.write('\n#Speed up sims for radio\n')
  file.write('#increase the energy threshold up to 3MeV (specially if you are not interested in the ground particles)..saves up to 50% time\n')
  file.write('ElectronCutEnergy 1 MeV\n')
  file.write('ElectronRoughCut 1 MeV\n')
  file.write('GammaCutEnergy 1 MeV\n')
  file.write('GammaRoughCut 1 MeV\n')
  file.write('\n#creates an additional CoREAS compatible output\n')
  file.write('CoREASOutput On\n')
  file.write('\n#removes from the fresnel time output the vector potential and the antena positions, leaving only antena number, time and electric field components\n')
  file.write('ReducedDATOutput On\n')
  file.write('################################################################################\n')
  file.write('End\n')
  file.write('################################################################################\n')

  file.close()


#this function reads he Aires .inp file and tries to extract information from the simulation parameters
#however, note that using the .sry file is preferred to using the .inp files because:
#Output is standirized: you dont know what you can find in an .inp file (leading spaces, commented lines, repeated keywords, etc)
#Output is what really happened, not what the user whishe it would happen when he did his crappy .inp file.
#This reader is oudated, and should be used with care


def ReadAiresInput(input_file,outmode):

    #there is a more pythonic way of opening files...but lets do things fast.
    #filepath = 'Iliad.txt'
    #with open(filepath) as fp:
    #for cnt, line in enumerate(fp):
    #   print("Line {}: {}".format(cnt, line))

    try:
      datafile=open(input_file,'r')
    except:
      print("file not found or invalid")

    print("this reader is updated and should be used with care")

    for line in datafile:
        ## print(line) #debug level 2

        if 'PrimaryZenAngle' in line:
            zen=float(line.split(' ',-1)[1])
            if outmode == 'GRAND':
                zen = 180-zen  #conversion to GRAND convention i.e. pointing towards antenna/propagtion direction
            print('Found Zenith',zen) #debug level 1

        if 'PrimaryAzimAngle' in line:
            azim = float(line.split(' ',-1)[1])
            if outmode == 'GRAND':
                azim = azim +180 #conversion to GRAND convention i.e. pointing towards antenna/propagtion direction
                if azim>=360:
                    azim= azim-360

            print('Found Azimuth',azim) #debug level 1

        if 'PrimaryEnergy' in line:
            energy = float(line.split(' ',-1)[1])
            unit= str(line.split(' ',-1)[2])

            if outmode == 'GRAND':
                if unit == "eV\n":
                    energy = energy *1e-18
                if unit == "KeV\n":
                    energy = energy *1e-15
                if unit == "MeV\n":
                    energy = energy *1e-12
                if unit == "GeV\n":
                    energy = energy *1e-9
                if unit == "TeV\n":
                    energy = energy *1e-6
                if unit == "PeV\n":
                    energy = energy *1e-3
                if unit == "EeV\n":
                    energy = energy

            if outmode == 'AIRES':
                if unit == "eV\n":
                    energy = energy *1e-9
                if unit == "KeV\n":
                    energy = energy *1e-6
                if unit == "MeV\n":
                    energy = energy *1e-3
                if unit == "GeV\n":
                    energy = energy
                if unit == "TeV\n":
                    energy = energy *1e3
                if unit == "PeV\n":
                    energy = energy *1e6
                if unit == "EeV\n":
                    energy = energy *1e9

            print('Found Energy',energy) #debug level 1

        if 'PrimaryParticle' in line:
            primarytype = str(line.split(' ',-1)[1])
            if primarytype[-1]=='\n':
                primarytype=primarytype[0:-1]
            print('Found Primary',primarytype) #debug level 1

    try:
        zen
    except NameError:
        zen = 0 #If no zenith angle was included in the input file, AIRES defaults to 0
        if outmode == 'GRAND':
          zen = 180-0 #that translates to 180 in GRAND
    try:
        azim
    except NameError:
        azim = 0 #If no azimuth angle was included in the input file, AIRES defaults to 0
        if outmode == 'GRAND':
          azim = 0+180 #that translates to 180
    try:
        energy
    except NameError:
        print('warning energy not found, Aires has no default value,  cannot continue')
        exit()
    try:
        primarytype
    except NameError:
        print('warning primary not found, Aires has no default value, cannot continue')
        exit()


    return zen,azim,energy,primarytype


if __name__ == '__main__':

  #All ZHAireS/Aires input files can be dividied in
  #Header (with parameters that frequently change from shower to shower: TaskName, pirmary, zenith, azimuth,energy,randomseed)
  #Antennas (and if we have antenas, then the ZHAireS ON and TimeFresne ON)
  #Rest of the input (all other input parameters, provided in a separate file, that must end with End)
  #so, an input file is generated by calling
  #CreateAiresInputHeader
  #Something for the antennas (CreateAiresStarShapeInp)
  #AddAiresSkeletonInp

  if np.size(sys.argv)<=4:
    print "Arguments = zen (deg, Zhaires) az (deg, Zhaires) slope (deg) slope azimuth (deg)."

  else:
    Zenith = float(sys.argv[1]) #in deg
    Azimuth = float(sys.argv[2]) #in deg
    alpha = float(sys.argv[3]) #in deg
    az_slope = float(sys.argv[4]) #in deg

    print "****Shower direction (zen, az) = ("+str(Zenith)+','+str(Azimuth) +") deg, Mountain slope = "+str(alpha)+","+str(az_slope)+" deg"

    Primary="Proton"
    TaskName="TestShower"
    Energy=0.123456789
    CreateAiresInputHeader(TaskName, Primary, Zenith, Azimuth, Energy)
    CreateAiresStarShapeInp(Zenith, Azimuth, alpha, az_slope,RandomFraction=0.1)
    CreateExampleSkeleton()






