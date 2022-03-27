import pydicom
import os
import sys
import cv2
from scipy.ndimage import gaussian_filter,rotate

class Dcm:
    def __init__(self, path):
        self.path = path
        self.ds = self._readImage()
        self.original = self.dcm_original()
        self.ipp = self.dcm_ipp()
        
    def dcm_original(self):
        pixel_data = self.ds.pixel_array
        return pixel_data
        
    def dcm_ipp(self):
        listImagePosition = self.ds.ImagePositionPatient._list
        return listImagePosition

    def _readImage(self):
        file_path = os.path.join(self.path)
        ds = pydicom.dcmread(file_path)
        return ds

class DcmFilter(Dcm):
    
    def __init__(self, path, sigma = 3):
        super().__init__(path)
        self.path = path
        self.sigma = sigma
        self.filtered = self.dcm_filtered()
        
    def dcm_filtered(self):
        pixel_data = self.ds.pixel_array
        filtered_image = gaussian_filter(pixel_data, self.sigma)
        return filtered_image
    
class DcmRotate(Dcm):
    
    def __init__(self, path, angle = 180):
        super().__init__(path)
        self.path = path
        self.angle = angle
        self.rotated = self.dcm_rotated()
        
    def dcm_rotated(self):
        if((self.angle % 90) != 0):
            print("Warning: only multiples of 90")
            sys.exit()
            
        pixel_data = self.ds.pixel_array
        data_rotated = rotate(pixel_data,self.angle)
        return data_rotated

class IncorrectNumberOfImages(Exception):
    """Incorrect number of images. Aborting."""
    pass

class SameImagePositionPatient(Exception):
    """The DICOM files appear to be the same. Aborting."""
    pass
    
def checkIpp(dcm1, dcm2):
    if(dcm1.ipp == dcm2.ipp):
        return True
    else:
        return False

def substraction(folder_path):
    try:
        files_list = os.listdir(folder_path)
        num_images = 0
        images = []
        for file in files_list:
            if os.path.isfile(os.path.join(folder_path, file)) and file.endswith('.dcm'):
                images.append(file)
                num_images = num_images + 1
                  
        if(num_images != 2):
            raise IncorrectNumberOfImages

        dcm1 = Dcm(folder_path + '/' + images[0])
        dcm2 = Dcm(folder_path + '/' + images[1])
        
        if(checkIpp(dcm1, dcm2) == True):
            raise SameImagePositionPatient
        
        unfiltered_residue = dcm1.original - dcm2.original
        
        im1_filtered = DcmFilter(folder_path + '/' + images[0]).filtered
        im2_filtered = DcmFilter(folder_path + '/' + images[1]).filtered
        
        filtered_residue = im1_filtered - im2_filtered
        
        residues_path = folder_path + '/residues'
        if (os.path.exists(folder_path) and not(os.path.exists(residues_path))):
            os.mkdir(residues_path)   
        
        unfiltered8U = cv2.convertScaleAbs(unfiltered_residue, alpha = (255.0/65535.0))
        filtered8U = cv2.convertScaleAbs(filtered_residue, alpha = (255.0/65535.0))
        
        cv2.imwrite(residues_path + '/unfiltered_residue.jpg', unfiltered8U)
        cv2.imwrite(residues_path + '/filtered_residue.jpg', filtered8U)
            
    except Exception as err:
        print(Exception, err.__doc__)
    
if __name__ == "__main__":
    args = sys.argv[1:]
    substraction(args[0])