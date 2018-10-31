import moderngl
from PIL import Image
import struct
import os
import numpy as np
from helpers.h import getScriptDir

PLUGIN_SETTINGS = {
 "NAME": "Shader Background",
 "DESCRIPTION": "Render shader to background",
 "CATEGORY": "GPU",
 "PLUGIN_FUNCS": {
	 "setShader": {
		 "NAME": "Set shader",
		 "DESCRIPTION": "Set the shader file to use",
		 "ARGUMENTS": {
			 "shader": {
				 "NAME": "Shader",
				 "DESCRIPTION": "Shader file",
				 "TYPE": "FILE .glsl|GLSL_Shader"
			 },
			 "shaderType": {
				 "NAME": "Shader type",
				 "DESCRIPTION": "The shader type (choose shadertoy for shadertoy shaders and vertexshaderart for vertexshaderart.com shaders)",
				 "TYPE": "DROPDOWN shadertoy vertexshaderart"
			 },
			 "vertexNum": {
				 "REQUIRES": "shaderType vertexshaderart",
				 "NAME": "Number of vertices",
				 "DESCRIPTION": "Set the number of vertices to render in vertexshaderart shaders",
				 "TYPE": "SLIDER 1 10000"
			 }
		 }
	 },
	 "setRenderMode": {
		 "NAME": "Set render mode for shader",
		 #"DESCRIPTION": ""
		 "ARGUMENTS": {
			 "renderMode": {
				 #"DESCRIPTION": ""
				 "TYPE": "DROPDOWN POINTS LINES LINE_STRIP LINE_LOOP TRIANGLES TRIANGLE_STRIP TRIANGLE_FAN"
			 }
		 }
	 }
 }
}


class Main():

	def __init__(self):
		with open(os.path.join(getScriptDir(), "shadertoyTemplate.txt"), "r") as shaderFile:
			shadersData = shaderFile.read().split("-----")
			self.shadertoy_vertex_template = shadersData[0]
			self.shadertoy_fragment_template = shadersData[1]
		with open(os.path.join(getScriptDir(), "vertexshaderartTemplate.txt"), "r") as shaderFile:
			shadersData = shaderFile.read().split("-----")
			self.vsa_vertex_template = shadersData[0]
			self.vsa_fragment_template = shadersData[1]
		# The context we will use for the shader
		self.glCtx = moderngl.create_standalone_context()
		self.glCtx.enable(moderngl.DEPTH_TEST)

	def setShader(self, shader, shaderType, vertexNum):
		self.shaderType = shaderType
		if shaderType == "shadertoy":
			# we have to remove the version directive from the shader and set the version of the other scripts
			# if there is no version directive, it still works
			glslVersion = ""
			hasVersionTag = False
			for line in shader.splitlines():
				if "#version" in line:
					glslVersion = line
					hasVersionTag = True
			if hasVersionTag:
				shader = shader.replace(glslVersion, "")
			else:
				glslVersion = "#version 130"  # safe estimate

			shaders = (self.shadertoy_vertex_template.format(version=glslVersion),
			           self.shadertoy_fragment_template.format(version=glslVersion, main_body=shader))

			self.program = self.glCtx.program(vertex_shader=shaders[0], fragment_shader=shaders[1])

			# time to initialize shader variables!
			self.safeSet("iMouse", (0.0, 0.0, 0.0, 0.0))
			self.safeSet("iSampleRate", 44100.0)
			for i in range(4):
				self.safeSet("iChannelTime[%d]" % i, 0.0)
			self.safeSet("iGlobalTime", 0)
			self.safeSet("iTime", 0)  # same thing
			self.time = 0.0  # just to be certain
			self.safeSet("iOffset", (0.0, 0.0))
			self.safeSet("iFrame", 0)

			# also time to create vertex array for rendering!
			# VBO is the position attribute passed to the vertex shader
			# it is the array of the vertices of the viewport
			position_var = struct.pack("8f", -1.0, 1.0, 1.0, 1.0, -1.0, -1.0, 1.0, -1.0)
			vbo = self.glCtx.buffer(position_var)
			self.vao = self.glCtx.simple_vertex_array(self.program, vbo, "position")
		elif shaderType == "vertexshaderart":
			glslVersion = "#version 130"
			shaders = (self.vsa_vertex_template.format(version=glslVersion, main_body=shader),
			           self.vsa_fragment_template.format(version=glslVersion))

			self.program = self.glCtx.program(vertex_shader=shaders[0], fragment_shader=shaders[1])

			# time to initialize shader variables!
			self.safeSet("vertexCount", 10000.0)  # sure, this will be changed later
			self.safeSet("mouse", (0.0, 0.0))
			self.safeSet("time", 0.0)
			self.time = 0.0  # just to be sure
			self.safeSet("background", (0.0, 0.0, 0.0, 1.0))  # just black
			self.safeSet("_dontUseDirectly_pointSize", 1)  # can be different, but is this for now

			self.glCtx.point_size = 1

			# also time to create vertex array for rendering!
			# VBO is the vertexId passed to the vertex shader
			# every vertex has an id, so that is passed here
			# otherOptions must be present and have number of vertices
			# this is the same output as struct.pack
			attributes = list()
			for i in range(0, vertexNum):
				attributes.append(i)
			vbo = self.glCtx.buffer(np.array(attributes).astype("f4").tobytes())
			self.vao = self.glCtx.simple_vertex_array(self.program, vbo, "vertexId")

	def setRenderMode(self, renderMode):
		modes = {
		 "POINTS": moderngl.POINTS,
		 "LINES": moderngl.LINES,
		 "LINE_STRIP": moderngl.LINE_STRIP,
		 "LINE_LOOP": moderngl.LINE_LOOP,
		 "TRIANGLES": moderngl.TRIANGLES,
		 "TRIANGLE_STRIP": moderngl.TRIANGLE_STRIP,
		 "TRIANGLE_FAN": moderngl.TRIANGLE_FAN
		}

		self.renderMode = modes.get(
		 renderMode, modes["TRIANGLE_STRIP"])  # will return TRIANGLE_STRIP if the mode doesnt exist

	def setResolution(self, width, height):
		# size is a tuple with width and height
		self.size = (width, height)
		# Texture where we render the scene.
		color_rbo = self.glCtx.renderbuffer(self.size)
		depth_rbo = self.glCtx.depth_renderbuffer(self.size)
		self.fbo = self.glCtx.framebuffer(color_rbo, depth_rbo)
		self.fbo.use()
		if self.shaderType == "shadertoy":
			self.safeSet("iResolution", (width, height, 0.0))
		elif self.shaderType == "vertexshaderart":
			self.safeSet("resolution", (width, height))
		# this is why the shader must be created before the size is changed!
		# also, when creating a new shader, change the resolution as well

	def setTime(self, time):
		# time is a float of the number of seconds since the start
		if self.shaderType == "shadertoy":
			self.safeSet("iGlobalTime", time)
			self.safeSet("iTime", time)
		elif self.shaderType == "vertexshaderart":
			self.safeSet("time", time)

	def render(self):
		self.glCtx.clear(0.0, 0.0, 0.0, 1.0)
		self.vao.render(mode=self.renderMode)
		return Image.frombytes('RGB', self.size, self.fbo.read()).transpose(Image.FLIP_TOP_BOTTOM)

	def setNextFrame(self, delta):  # could be a duplicate of setTime
		self.time += delta
		self.setTime(self.time)

	def renderNextFrame(self, delta):
		# this is the function that the main file can read
		# required
		self.setNextFrame(delta)
		return self.render()

	def safeSet(self, key, value):
		try:
			self.program[key].value = value
		except KeyError:
			# no need, the uniform simply does not exist
			pass

	def safeGet(self, key):
		try:
			return self.program[key].value
		except KeyError:
			# no need, the uniform simply does not exist
			pass