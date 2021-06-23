//------------------------------------------------------------------------------
// Copyright Chris Eykamp
// See LICENSE.txt for full copyright information
//------------------------------------------------------------------------------

#include "GLFixedRenderer.h"
#include "DisplayManager.h"
#include "Color.h"
#include "Point.h"
#include "tnlVector.h"
#include "SDL_opengl.h" // Basic OpenGL support

namespace Zap
{

// Private
GLFixedRenderer::GLFixedRenderer()
{
   glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
   glEnable(GL_SCISSOR_TEST);    // Turn on clipping
   glEnable(GL_BLEND);
}

GLFixedRenderer::~GLFixedRenderer()
{
   
}

U32 GLFixedRenderer::getGLRenderType(RenderType type) const
{
   switch(type)
   {
   case RenderType::Points:
      return GL_POINTS;

   case RenderType::Lines:
      return GL_LINES;

   case RenderType::LineStrip:
      return GL_LINE_STRIP;

   case RenderType::LineLoop:
      return GL_LINE_LOOP;

   case RenderType::Triangles:
      return GL_TRIANGLES;

   case RenderType::TriangleStrip:
      return GL_TRIANGLE_STRIP;

   case RenderType::TriangleFan:
      return GL_TRIANGLE_FAN;

   default:
         return 0;
   }
}

U32 GLFixedRenderer::getGLTextureFormat(TextureFormat format) const
{
   switch(format)
   {
   case TextureFormat::RGB:
      return GL_RGB;

   case TextureFormat::RGBA:
      return GL_RGBA;

   default:
      return 0;
   }
}

U32 GLFixedRenderer::getGLDataType(DataType type) const
{
   switch(type)
   {
   case DataType::UnsignedByte:
      return GL_UNSIGNED_BYTE;

   case DataType::Byte:
      return GL_BYTE;

   case DataType::UnsignedShort:
      return GL_UNSIGNED_SHORT;

   case DataType::Short:
      return GL_SHORT;

   case DataType::UnsignedInt:
      return GL_UNSIGNED_INT;

   case DataType::Int:
      return GL_INT;

   case DataType::Float:
      return GL_FLOAT;

   default:
      return 0;
   }
}

// Static
void GLFixedRenderer::create()
{
   setInstance(std::unique_ptr<Renderer>(new GLFixedRenderer));
}

void GLFixedRenderer::clear()
{
   glClear(GL_COLOR_BUFFER_BIT);
}

void GLFixedRenderer::setClearColor(F32 r, F32 g, F32 b, F32 alpha)
{
   glClearColor(r, g, b, alpha);
}

void GLFixedRenderer::setColor(F32 r, F32 g, F32 b, F32 alpha)
{
   glColor4f(r, g, b, alpha);
}

void GLFixedRenderer::setLineWidth(F32 width)
{
   glLineWidth(width);
}

void GLFixedRenderer::setPointSize(F32 size)
{
   glPointSize(size);
}

void GLFixedRenderer::setViewport(S32 x, S32 y, S32 width, S32 height)
{
   glViewport(x, y, width, height);
}

Point GLFixedRenderer::getViewportPos()
{
   GLint viewport[4];
   glGetIntegerv(GL_VIEWPORT, viewport);

   return Point(viewport[0], viewport[1]);
}

Point GLFixedRenderer::getViewportSize()
{
   GLint viewport[4];
   glGetIntegerv(GL_VIEWPORT, viewport);

   return Point(viewport[2], viewport[3]);
}

void GLFixedRenderer::scale(F32 x, F32 y, F32 z)
{
   glScalef(x, y, z);
}

void GLFixedRenderer::translate(F32 x, F32 y, F32 z)
{
   glTranslatef(x, y, z);
}

void GLFixedRenderer::rotate(F32 angle, F32 x, F32 y, F32 z)
{
   glRotatef(angle, x, y, z);
}

void GLFixedRenderer::setMatrixMode(MatrixType type)
{
   switch (type)
   {
   case MatrixType::ModelView:
      glMatrixMode(GL_MODELVIEW);
      break;

   case MatrixType::Projection:
      glMatrixMode(GL_PROJECTION);
      break;

   default:
      break;
   }
}

void GLFixedRenderer::getMatrix(MatrixType type, F32* matrix)
{
   switch (type)
   {
   case MatrixType::ModelView:
      glGetFloatv(GL_MODELVIEW_MATRIX, matrix);
      break;

   case MatrixType::Projection:
      glGetFloatv(GL_PROJECTION_MATRIX, matrix);
      break;

   default:
      break;
   }
}

void GLFixedRenderer::pushMatrix()
{
   glPushMatrix();
}

void GLFixedRenderer::popMatrix()
{
   glPopMatrix();
}

void GLFixedRenderer::loadMatrix(const F32* m)
{
   glLoadMatrixf(m);
}

void GLFixedRenderer::loadMatrix(const F64* m)
{
   glLoadMatrixd(m);
}

void GLFixedRenderer::loadIdentity()
{
   glLoadIdentity();
}

void GLFixedRenderer::projectOrtho(F64 left, F64 right, F64 bottom, F64 top, F64 nearx, F64 farx)
{
   glOrtho(left, right, bottom, top, nearx, farx);
}

U32 GLFixedRenderer::generateTexture()
{
   GLuint textureHandle;
   glGenTextures(1, &textureHandle);
   return textureHandle;
}

bool GLFixedRenderer::isTexture(U32 textureHandle)
{
   return glIsTexture(textureHandle);
}

void GLFixedRenderer::deleteTexture(U32 textureHandle)
{
   glDeleteTextures(1, &textureHandle);
}

void GLFixedRenderer::setTextureData(TextureFormat format, DataType dataType, U32 width, U32 height, const void* data)
{
   glTexImage2D(
      GL_TEXTURE_2D, 0, GL_RGB,
      width, height, 0,
      getGLTextureFormat(format), getGLDataType(dataType), data);
}

void GLFixedRenderer::renderVertexArray(const S8 verts[], S32 vertCount, RenderType type, U32 start, U32 stride)
{
   glEnableClientState(GL_VERTEX_ARRAY);

   glVertexPointer(2, GL_BYTE, stride, verts);
   glDrawArrays(getGLRenderType(type), start, vertCount);

   glDisableClientState(GL_VERTEX_ARRAY);
}

void GLFixedRenderer::renderVertexArray(const S16 verts[], S32 vertCount, RenderType type, U32 start, U32 stride)
{
   glEnableClientState(GL_VERTEX_ARRAY);

   glVertexPointer(2, GL_SHORT, stride, verts);
   glDrawArrays(getGLRenderType(type), start, vertCount);

   glDisableClientState(GL_VERTEX_ARRAY);
}

void GLFixedRenderer::renderVertexArray(const F32 verts[], S32 vertCount, RenderType type, U32 start, U32 stride)
{
   glEnableClientState(GL_VERTEX_ARRAY);

   glVertexPointer(2, GL_FLOAT, stride, verts);
   glDrawArrays(getGLRenderType(type), start, vertCount);

   glDisableClientState(GL_VERTEX_ARRAY);
}

void GLFixedRenderer::renderColored(const F32 verts[], const F32 colors[], S32 vertCount, RenderType type)
{
   glEnableClientState(GL_VERTEX_ARRAY);
   glEnableClientState(GL_COLOR_ARRAY);

   glVertexPointer(2, GL_FLOAT, 0, verts);
   glColorPointer(4, GL_FLOAT, 0, colors);
   glDrawArrays(getGLRenderType(type), 0, vertCount);

   glDisableClientState(GL_COLOR_ARRAY);
   glDisableClientState(GL_VERTEX_ARRAY);
}

void GLFixedRenderer::renderTextured(const F32 verts[], const F32 UVs[], U32 vertCount, RenderType type, U32 start, U32 stride)
{
   // !Todo properly!
   glEnable(GL_TEXTURE_2D);
   glEnableClientState(GL_VERTEX_ARRAY);
   glEnableClientState(GL_TEXTURE_COORD_ARRAY);

   glVertexPointer(2, GL_FLOAT, stride, verts);
   glTexCoordPointer(2, GL_FLOAT, stride, UVs);
   glDrawArrays(GL_TRIANGLES, 0, vertCount);

   glDisable(GL_TEXTURE_2D);
   glDisableClientState(GL_VERTEX_ARRAY);
   glDisableClientState(GL_TEXTURE_COORD_ARRAY);
}

void GLFixedRenderer::renderColoredTexture(const F32 verts[], const F32 UVs[], U32 vertCount, RenderType type, U32 start, U32 stride)
{
   // !Todo properly!
   glEnable(GL_TEXTURE_2D);
   glEnableClientState(GL_VERTEX_ARRAY);
   glEnableClientState(GL_TEXTURE_COORD_ARRAY);

   glVertexPointer(2, GL_FLOAT, stride, verts);
   glTexCoordPointer(2, GL_FLOAT, stride, UVs);
   glDrawArrays(GL_TRIANGLES, 0, vertCount);

   glDisable(GL_TEXTURE_2D);
   glDisableClientState(GL_VERTEX_ARRAY);
   glDisableClientState(GL_TEXTURE_COORD_ARRAY);
}

}