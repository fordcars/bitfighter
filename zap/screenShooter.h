

#ifndef _SCREENSHOOTER_H_
#define _SCREENSHOOTER_H_

#include "../tnl/tnl.h"
#include <sys/stat.h>   // For checking screenshot folder

using namespace TNL;

namespace Zap
{
/*
 * Windows BMP file definitions for OpenGL.
 *
 * Written by Michael Sweet.
 */

#define  _CRT_TERMINATE_DEFINED     // Avoid incompatiblities btwn MSVC++ and GLUT
/*
 * Include necessary headers.
 */

#ifndef ZAP_DEDICATED
#   ifdef _APPLE_
#      include <GLUT/glut.h>
#   else
#      include <../glut/glut.h>         // Needed for Windows and Linux
#   endif
#endif

#ifdef WIN32
#   include <windows.h>
#   include <wingdi.h>
#   define _CRT_SECURE_NO_DEPRECATE    // Avoid warnings about fopen
#endif /* WIN32 */

/*
 * Make this header file work with C and C++ source code...
 */

#  ifdef __cplusplus
extern "C" {
#  endif /* __cplusplus */


/*
 * Bitmap file data structures (these are defined in <wingdi.h> under
 * Windows...)
 *
 * Note that most Windows compilers will pack the following structures, so
 * when reading them under MacOS or UNIX we need to read individual fields
 * to avoid differences in alignment...
 */

#  ifndef WIN32
typedef struct                       /**** BMP file header structure ****/
    {
    unsigned short bfType;           /* Magic number for file */
    unsigned int   bfSize;           /* Size of file */
    unsigned short bfReserved1;      /* Reserved */
    unsigned short bfReserved2;      /* ... */
    unsigned int   bfOffBits;        /* Offset to bitmap data */
    } BITMAPFILEHEADER;

#  define BF_TYPE 0x4D42             /* "MB" */

typedef struct                       /**** BMP file info structure ****/
    {
    unsigned int   biSize;           /* Size of info header */
    int            biWidth;          /* Width of image */
    int            biHeight;         /* Height of image */
    unsigned short biPlanes;         /* Number of color planes */
    unsigned short biBitCount;       /* Number of bits per pixel */
    unsigned int   biCompression;    /* Type of compression to use */
    unsigned int   biSizeImage;      /* Size of image data */
    int            biXPelsPerMeter;  /* X pixels per meter */
    int            biYPelsPerMeter;  /* Y pixels per meter */
    unsigned int   biClrUsed;        /* Number of colors used */
    unsigned int   biClrImportant;   /* Number of important colors */
    } BITMAPINFOHEADER;

/*
 * Constants for the biCompression field...
 */

#  define BI_RGB       0             /* No compression - straight BGR data */
#  define BI_RLE8      1             /* 8-bit run-length compression */
#  define BI_RLE4      2             /* 4-bit run-length compression */
#  define BI_BITFIELDS 3             /* RGB bitmap with RGB masks */

typedef struct                       /**** Colormap entry structure ****/
    {
    unsigned char  rgbBlue;          /* Blue value */
    unsigned char  rgbGreen;         /* Green value */
    unsigned char  rgbRed;           /* Red value */
    unsigned char  rgbReserved;      /* Reserved */
    } RGBQUAD;

typedef struct                       /**** Bitmap information structure ****/
    {
    BITMAPINFOHEADER bmiHeader;      /* Image header */
    RGBQUAD          bmiColors[256]; /* Image colormap */
    } BITMAPINFO;
#  endif /* !WIN32 */

/*
 * Prototypes...
 */

#ifndef ZAP_DEDICATED
extern GLubyte *LoadDIBitmap(const char *filename, BITMAPINFO **info);
extern int     SaveDIBitmap(const char *filename, BITMAPINFO *info, GLubyte *bits);
#endif

#  ifdef __cplusplus
}
#  endif /* __cplusplus */


class Screenshooter 
{
private:
   S32 mWidth;
   S32 mHeight;

public: 
   S32 phase;

   Screenshooter()    // Constructor
   {
      this->phase = 0;
   }

   // Save a TGA-format screenshot.  We do this in two phases because we get better screenshots if the window is exactly 800x600, 
   // so we want to resize.  We need to wait one cycle after resizing to ensure the screen is repainted for us to capture.  This
   // is unfortunate in that it creates a jarring experience for the user, but I think it is worth it.
   void saveScreenshot();
  
};


}


#endif /* !_SCREENSHOOTER_H_ */
