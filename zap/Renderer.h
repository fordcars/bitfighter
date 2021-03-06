//------------------------------------------------------------------------------
// Copyright Chris Eykamp
// See LICENSE.txt for full copyright information
//------------------------------------------------------------------------------

// Singleton class for Rendering APIS. I wish this wasn't a Singleton, but the lack of OOP
// in some areas of Bitfighter has forced my hand!

#ifndef _RENDERER_H_
#define _RENDERER_H_

#include "tnlTypes.h"
#include "tnlAssert.h"
#include <memory>

namespace TNL {
   template<class T> class Vector;
};

using namespace TNL;

namespace Zap
{

class Color;
class Point;

enum class MatrixType
{
   ModelView,
   Projection
};

enum class RenderType
{
   Points,
   Lines,
   LineStrip,
   LineLoop,
   Triangles,
   TriangleStrip,
   TriangleFan,
   Quads
};

enum class TextureFormat
{
    RGB,
    RGBA
};

enum class DataType
{
    UnsignedByte,
    Byte,
    UnsignedShort,
    Short,
    UnsignedInt,
    Int,
    Float
};

class Renderer
{
private:
   static std::unique_ptr<Renderer> mInstance;

   // Make these inaccessible:
   Renderer(const Renderer&) = default;
   Renderer& operator=(const Renderer&) = default;

protected:
   Renderer() = default; // Constructor is accessible only to derived classes.
   static void setInstance(std::unique_ptr<Renderer>&& instance);

public:
   virtual ~Renderer() = default;
   static Renderer& get();

   void setColor(F32 c, F32 alpha = 1.0f);
   void setColor(const Color& c, F32 alpha = 1.0f);

   void translate(const Point& offset);
   void rotate(F32 angle);
   void scale(F32 factor);
   void scale(const Point& factor);

   void renderPointVector(const Vector<Point>* points, RenderType type);
   void renderPointVector(const Vector<Point>* points, const Point& offset, RenderType type);

   // Implemented by concrete renderers:
   virtual void clear() = 0;
   virtual void setClearColor(F32 r, F32 g, F32 b, F32 alpha = 1.0f) = 0;
   virtual void setColor(F32 r, F32 g, F32 b, F32 alpha = 1.0f) = 0;
   
   virtual void setLineWidth(F32 width) = 0;
   virtual void setPointSize(F32 size) = 0;
   virtual void setViewport(S32 x, S32 y, S32 width, S32 height) = 0;
   virtual Point getViewportPos() = 0;
   virtual Point getViewportSize() = 0;

   virtual void scale(F32 x, F32 y, F32 z = 1.0f) = 0;
   virtual void translate(F32 x, F32 y, F32 z = 0.0f) = 0;
   virtual void rotate(F32 angle, F32 x, F32 y, F32 z) = 0;

   virtual void setMatrixMode(MatrixType type) = 0;
   virtual void getMatrix(MatrixType type, F32* matrix) = 0;
   virtual void pushMatrix() = 0;
   virtual void popMatrix() = 0;
   virtual void loadMatrix(const F32* m) = 0;
   virtual void loadMatrix(const F64* m) = 0;
   virtual void loadIdentity() = 0;
   virtual void projectOrtho(F64 left, F64 right, F64 bottom, F64 top, F64 nearx, F64 farx) = 0;

   // Textures
   virtual U32 generateTexture() = 0;
   virtual void bindTexture(U32 textureHandle) = 0;
   virtual bool isTexture(U32 textureHandle) = 0;
   virtual void deleteTexture(U32 textureHandle) = 0;
   virtual void setTextureData(TextureFormat format, DataType dataType, U32 width, U32 height, const void* data) = 0;


   // Render points:
   virtual void renderVertexArray(const S8 verts[], U32 vertCount, RenderType type,
      U32 start = 0, U32 stride = 0, U32 vertDimension = 2) = 0;
   virtual void renderVertexArray(const S16 verts[], U32 vertCount, RenderType type,
      U32 start = 0, U32 stride = 0, U32 vertDimension = 2) = 0;
   virtual void renderVertexArray(const F32 verts[], U32 vertCount, RenderType type,
      U32 start = 0, U32 stride = 0, U32 vertDimension = 2) = 0;

   // Render RGBA colored vertices
   virtual void renderColored(const F32 verts[], const F32 colors[], U32 vertCount,
      RenderType type, U32 start = 0, U32 stride = 0, U32 vertDimension = 2) = 0;

   virtual void renderTextured(const F32 verts[], const F32 UVs[], U32 vertCount,
      RenderType type, U32 start = 0, U32 stride = 0, U32 vertDimension = 2) = 0;

   // Render a texture colored by the current color:
   virtual void renderColoredTexture(const F32 verts[], const F32 UVs[], U32 vertCount,
      RenderType type, U32 start = 0, U32 stride = 0, U32 vertDimension = 2) = 0;
};


}

#endif /* _RENDERER_H_ */