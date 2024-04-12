# Inazuma Eleven Victory Road (Nintendo Switch)
# Noesis script adapted by Daiki froms DKDave's Yokai Watch 4 script
# Load meshes from both .G4PKM and .G4MD files
# Last updated: 12 April  2024

# TO DO LIST:

# Possibily some textures are loading wrong
# Add skeleton


from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Inazuma Eleven Victory Road (Switch)",".g4pkm;.g4md")
	noesis.setHandlerTypeCheck(handle, bcCheckType)
	noesis.setHandlerLoadModel(handle, bcLoadModel)
	noesis.logPopup()
	return 1


# Check file type

def bcCheckType(data):
	bs = NoeBitStream(data)
	file_id = bs.readUInt()

	if file_id == 0x4b503447 or file_id == 0x444d3447:
		return 1
	else:
		return 0


def bcLoadModel(data, mdlList):
	bs = NoeBitStream(data)
	ctx = rapi.rpgCreateContext()

	curr_folder = rapi.getDirForFilePath(rapi.getInputName()).lower()
	curr_file = rapi.getLocalFileName(rapi.getInputName()).lower()

	bones = []

	filename = curr_file.split(".")[0]
	vert_file = filename + ".g4mg"
	tex_file = filename + ".g4tx"

	if ".g4pkm" in curr_file:
		bs.seek(0x48)
		skel_size = bs.readUInt()
		bs.seek(0x80)
		sk = NoeBitStream(bs.readBytes(skel_size))

# For some models, the G4MD inside the G4PKM file doesn't work, but the separate G4MD file does (if it exists), so load that instead

		if rapi.checkFileExists(curr_folder + filename + ".g4md"):
			md = NoeBitStream(rapi.loadIntoByteArray(curr_folder + filename + ".g4md"))
			print("External G4MD file loaded")
		else:
			offset = data.find(b'G4MD')
			bs.seek(offset + 0x0c)
			md_size = bs.readUInt() + 0xa0
			bs.seek(offset)
			md = NoeBitStream(bs.readBytes(md_size))

	else:
		md = NoeBitStream(bs.readBytes(len(data)))



# Load vertex data file if it exists (or exit if not)

	if rapi.checkFileExists(curr_folder + vert_file):
		vf = NoeBitStream(rapi.loadIntoByteArray(curr_folder + vert_file))
		print("Geometry data file loaded.")
	else:
		print("Vertex data file " + vert_file + " doesn't exist.")
		return 1


# Read the mesh data

	md.seek(4)
	submesh_info = md.readUShort()
	md.seek(0x20)
	submesh_count = md.readUShort()
	mat_count = md.readUShort()
	md.seek(0x26)
	vlayout_count = md.readUByte()
	md.seek(0x5c)
	face_data = md.readUInt()

	vlayout_offs = []
	vnames = ["", "Verts", "Normals", "", "", "", "", "", "Colours", "", "UV", "UV2", "UV3", "UV4", "UV5", "UV6"]
	vlayout = (submesh_count * 0x50) + submesh_info
	md.seek(vlayout)

	for v in range(vlayout_count):
		vlayout_offs.append(md.tell())
		md.readUByte()
		entry_count = md.readUByte()
		md.readBytes(6)
		md.seek(entry_count * 8, 1)

	mat_table = md.tell()							# how to calculate this without reading vlayout table first?
	mat_table = Align(mat_table, 16)
	mat_table2 = mat_table + (mat_count * 0x10) + 0x30


# Load texture archive if it exists, and create materials
# Some of this could be completely wrong ...

	if rapi.checkFileExists(curr_folder + filename + ".g4tx"):
		tx = NoeBitStream(rapi.loadIntoByteArray(curr_folder + tex_file))
		print("Texture data file loaded.")
		tex_list, tex_names = ReadTextures(tx)
		mat_list = []

		for m in range(mat_count):
			md.seek(mat_table + (m * 0x10) + 12)
			mcount = md.readUShort()
			mstart = md.readUShort()

			temp_list = []
			for x in range(mcount):
				md.seek(mat_table2 + (mstart * 6) + (x * 6))
				mnum = md.readUByte()
				temp_list.append(mnum)

			material = NoeMaterial("Mat_" + str(m), "")
			print(temp_list)
			if len(temp_list) == 6:
				diff = temp_list[5]
				spec = temp_list[4]
				occ =  temp_list[3]
				material.setTexture(tex_names[diff])
				material.setSpecularTexture(tex_names[spec])
				material.setOcclTexture(tex_names[occ])

			if len(temp_list) == 5:
				diff = temp_list[1] if filename[0] == "c" else temp_list[4]
				spec = temp_list[0]
				occ =  temp_list[2]
				material.setTexture(tex_names[diff])
				material.setSpecularTexture(tex_names[spec])
				material.setOcclTexture(tex_names[occ])
			
			if len(temp_list) == 4:
				print(temp_list)
				diff = temp_list[3]
				#spec = temp_list[]
				material.setTexture(tex_names[diff])
				#material.setSpecularTexture(tex_names[spec])

			if len(temp_list) == 3:
				diff = temp_list[2]
				material.setTexture(tex_names[0])
			

			mat_list.append(material)

	else:
		print("Texture data file " + tex_file + " doesn't exist.  No textures will be available.")
		tex_list = []
		mat_list = []


	for a in range(submesh_count):
		md.seek(submesh_info + (a * 0x50))
		misc1 = md.tell()
		vert_offset = md.readUInt()
		face_offset = md.readUInt() + face_data
		vert_count = md.readUInt()
		face_count = md.readUInt()
		md.seek(0x2e, 1)
		stride = md.readUByte()
		md.seek(3, 1)
		layout_num = md.readUByte()
		mat_num = md.readUByte()

		print("--------------------------------------------------------------------------------")
		print(a, "\t", hex(vert_offset), "\t", hex(face_offset), "\t", vert_count, "\t", face_count, "\t", hex(stride), mat_num, layout_num)
		print("--------------------------------------------------------------------------------")

		if face_count != 0:
			vf.seek(vert_offset)
			vertices = vf.readBytes(vert_count * stride)

			rapi.rpgSetName(filename + "_" + str(a))
			rapi.rpgSetMaterial("Mat_" + str(mat_num))

			layout_offset = vlayout_offs[layout_num]			# doesn't always work?
			md.seek(layout_offset+1)
			entry_count = md.readUByte()
			md.readBytes(6)

			for x in range(entry_count):
				vtype = md.readUByte()
				vtype_off = md.readUShort()
				md.readUByte()
				vtype_num = md.readUInt()

				print(x, "\t", vnames[vtype], "\t", vtype_off, "\t", vtype_num)

				if vtype_num == 2 or vtype_num == 3:
					vert_num = noesis.RPGEODATA_FLOAT
				elif vtype_num == 12:
					vert_num = noesis.RPGEODATA_UBYTE
				elif vtype_num == 14:
					vert_num = noesis.RPGEODATA_USHORT
				elif vtype_num == 20 or vtype_num == 18:
					vert_num = noesis.RPGEODATA_SHORT


				if vtype == 1:
					rapi.rpgBindPositionBufferOfs(vertices, vert_num, stride, vtype_off)
				elif vtype == 2:
					rapi.rpgBindNormalBufferOfs(vertices, vert_num, stride, vtype_off)
#				elif vtype == 8:
#					rapi.rpgBindColorBufferOfs(vertices, vert_num, stride, vtype_off, 4)
				elif vtype == 10:				
						rapi.rpgBindUV1BufferOfs(vertices, vert_num, stride, vtype_off)



			vf.seek(face_offset)

			if vert_count > 65535:
				faces = vf.readBytes(face_count * 4)
				rapi.rpgCommitTriangles(faces, noesis.RPGEODATA_UINT, face_count, noesis.RPGEO_TRIANGLE)
			else:
				faces = vf.readBytes(face_count * 2)
				rapi.rpgCommitTriangles(faces, noesis.RPGEODATA_USHORT, face_count, noesis.RPGEO_TRIANGLE)

			rapi.rpgClearBufferBinds()

	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()

	mdl.setModelMaterials(NoeModelMaterials(tex_list, mat_list))
#	mdl.setBones(bones)
	mdlList.append(mdl)

	return 1



def Align(value, div):
	mod = value % div

	if mod > 0:
		value += (div - mod)

	return value



# Read textures

def ReadTextures(bs):
	print("Reading textures")

	tex_list = []
	tex_names = []

	bs.seek(0x20)
	tex_count = bs.readUShort()

	name_off = (tex_count * 0x30) + 0x60 + (tex_count * 4) + tex_count
	name_off = Align(name_off, 4)

	bs.seek(name_off)

	for n in range(tex_count):
		bs.seek(name_off + (n * 2))
		text_off = bs.readUShort() + name_off
		bs.seek(text_off)
		tex_names.append(bs.readString())

	bs.seek(0x0c)
	data_start = bs.readUInt() + 0x60
	data_start = Align(data_start, 0x10)

	for t in range(tex_count):
		bs.seek((t * 0x30) + 0x64)
		offset = bs.readUInt() + data_start
		size = bs.readUInt()
		bs.seek(offset + 0x8)
		data_size = bs.readUInt()
		bs.readUInt()
		bs.readUInt()
		width = bs.readUInt()
		height = bs.readUInt()

		bs.seek(offset + 0x100)
		raw_image = bs.readBytes(data_size)

		blockwidth = blockheight = 4
		widthinblocks = (width + (blockwidth - 1)) // blockwidth
		heightinblocks = (height + (blockheight - 1)) // blockheight

		blockSize = 16 if width >= 1024 else 16

		maxblockheight = 16 if width >= 512 and height <= 512 else 16
		maxblockheight = 8 if width <= 512 and height <= 256 else 16
		maxblockheight = 8 if width <= 256 and height <= 256 else maxblockheight
		maxblockheight = 4 if width <= 256 and height <= 128 else maxblockheight
		maxblockheight = 4 if width <= 128 or height <= 64 else maxblockheight
		maxblockheight = 1 if width <= 64 or height <= 32 else maxblockheight
		
		raw_image = rapi.callExtensionMethod("untile_blocklineargob", raw_image, widthinblocks, heightinblocks, blockSize, maxblockheight)
		raw_image = rapi.imageDecodeDXT(raw_image, width, height, noesis.FOURCC_BC7)				# always BC7
		tex1 = NoeTexture(tex_names[t], width, height, raw_image, noesis.NOESISTEX_RGBA32)

		print("{0:<15x}{1:<15x}{2:<15x}{3:<15}{4:<15}".format(offset, size, data_size, width, height))

		tex_list.append(tex1)

	return tex_list, tex_names


