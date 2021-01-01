# This script preprocesses our C++ code and generates fodder for Doxygen which makes pretty documentation
# for our Lua scripters out there

# Works with doxygen verison 1.9.0

import os
from glob import glob
import re
import subprocess
from typing import List, Any, Dict, Optional, Tuple
from lxml import etree
from datetime import datetime

# Need to be in the doc directory
doc_dir = "doc"
outpath = os.path.join(os.path.dirname(__file__), doc_dir)

if not os.path.exists(outpath):
    raise Exception("Could not change to doc folder: $!")

# Relative path where intermediate outputs will be written
outpath = os.path.join(outpath, "temp-doxygen")

# Create it if it doesn't exist
if not os.path.exists(outpath):
    os.makedirs(outpath)


doxygen_cmd = r"C:\Program Files\doxygen\bin\doxygen.exe"


# These are items we collect and build up over all pages, and they will get written to a special .h file at the end
mainpage = []
enums = []

FUNCS_HEADER_MARKER = "DummyConstructor"

NBSP = "&#160;"


def main():
    # Collect some file names to process
    files = []

    files.extend(glob(os.path.join(outpath, "../../zap/*.cpp")))               # Core .cpp files
    files.extend(glob(os.path.join(outpath, "../../zap/*.h")))                 # Core .h files
    files.extend(glob(os.path.join(outpath, "../../lua/lua-vec/src/*.c")))     # Lua-vec .c files  -- none here anymore... can probably delete this line
    files.extend(glob(os.path.join(outpath, "../../resource/scripts/*.lua")))  # Some Lua scripts
    files.extend(glob(os.path.join(outpath, "../static/*.txt")))               # our static pages for general information and task-specific examples


    # files = [r"C:\dev\bitfighter/zap/ship.cpp"]

    parse_files(files)
    run_doxygen()
    post_process()

class EnumMode:
    NOT_COLLECTING = 0
    LUA_ENUM_COMMENT = 1
    CPP_DEFINE = 2


def parse_files(files: List[str]):
    # Loop through all the files we found above...
    for file in files:
        print(f"Processing {os.path.basename(file)}...")

        with open(file, "r") as filex:

            enumIgnoreColumn = None
            enumName = "XXXXX"
            enumColumn = "XXXXX"

            # Various modes we could be in
            collectingMethods = 0
            collectingStaticMethods = 0
            # collectingLongDescr = 0
            processing_long_comment = False
            processing_main_page = False
            collectingEnumMode = EnumMode.NOT_COLLECTING
            descrColumn = 0
            encounteredDoxygenCmd = False

            luafile = file.endswith(".lua")   # Are we processing a .lua file?

            methods = []
            staticMethods = []
            globalfunctions = []
            comments = []
            classes = {}         # Will be a dict of arrays

            shortClassDescr = ""
            longClassDescr  = ""

            # Visit each line of the source cpp file
            for line_num, line in enumerate(filex):

                # If we are processing a .lua file, replace @luaclass with @luavclass for simplicity
                if luafile:
                    line = line.replace("@luaclass", "@luavclass")

                #####
                # LUA BASE CLASSES in C++ code
                #####
                match = re.search(r"REGISTER_LUA_CLASS *\( *(.+?) *\)", line)
                if match:
                    xclass = match.groups()[0]
                    if xclass not in classes:
                        classes[xclass] = []

                    classes[xclass].insert(0, f"{shortClassDescr}\n{longClassDescr}\nclass {xclass} {{ \n public:\n")
                    continue

                #####
                # LUA SUBCLASSES in C++ code
                #####
                match = re.search(r"REGISTER_LUA_SUBCLASS *\( *(.+?) *, *(.+?) *\)", line)
                if match:
                    xclass = match.groups()[0]
                    parent = match.groups()[1]
                    if xclass not in classes:
                        classes[xclass] = []
                    classes[xclass].insert(0, f"{shortClassDescr}\n{longClassDescr}\nclass {xclass} : public {parent} {{ \n public:\n")
                    shortClassDescr = ""
                    longClassDescr = ""
                    continue


                #####
                # LUA METHODS block in C++ code
                #####

                def make_method_line(method_name: str) -> str:
                    return f"void {method_name}() {{ }}\n"

                match = re.search(r"define +LUA_METHODS *\(CLASS, *METHOD\)", line)
                if match:
                    collectingMethods = True        # Activate collecting methods mode
                    continue

                if collectingMethods:
                    match = re.search(r"METHOD *\( *CLASS, *(.+?) *,", line)                 # Signals class declaration... methods will follo
                    if match:
                        methods.append(match.groups()[0])
                        continue

                    match = re.search(r"GENERATE_LUA_METHODS_TABLE *\( *(.+?) *,", line)      # Signals we have all methods for this class, gives us class name; now generate cod
                    if match:
                        xclass = match.groups()[0]

                        for method in methods:
                            if xclass not in classes:
                                classes[xclass] = []
                            classes[xclass].append(make_method_line(method))

                        methods = []
                        collectingMethods = False
                        continue

                match = re.search(r"define +LUA_STATIC_METHODS *\( *METHOD *\)", line)
                if match:
                    collectingStaticMethods = True
                    continue


                if collectingStaticMethods:
                    match = re.search(r"METHOD *\( *(.+?) *,", line)                 # Signals class declaration... methods will follow
                    if match:
                        method = match.groups()[0]
                        staticMethods.append(method + "\n")
                        continue

                    match = re.search(r"GENERATE_LUA_STATIC_METHODS_TABLE *\( *(.+?) *,", line)  # Signals we have all methods for this class, gives us class name; now generate cod
                    if match:
                        xclass = match.groups()[0]

                        if xclass not in classes:
                            classes[xclass] = []

                        # This becomes our "constructor"
                        classes[xclass].insert(0, f"{shortClassDescr}\n{longClassDescr}\nclass {xclass} {{ \npublic:\n")

                        # This is an ordinary "class method"
                        for method in staticMethods:
                            # index = first { ${$classes{$class}}[$_] =~ m|\s$method\(| } 0..$#{$classes{$class}}  # ? Not sure what's happening here
                            index = False       # TODO: Fix line above

                            found = False
                            for xxx in classes[xclass]:
                                if re.search(f"\\s{method}\\(", xxx):       # ? Maybe this is it??
                                    found = True
                                    break

                            # Ignore methods that already have explicit documentation
                            if not found:
                                classes[xclass].append(f"static void {method}() {{ }}\n")

                        staticMethods = []
                        collectingStaticMethods = False
                        continue

                #####
                # LONG COMMENTS (anything starting with "/**" in C++ or "--[[" in Lua)
                # These tokens signal we're entering the beginning of a long comment block we need to pay attention to
                comment_pattern = r"--\[\[" if luafile else r"/\*\*"
                if re.search(comment_pattern, line):
                    processing_long_comment = True
                    comments.append("/*!\n")
                    continue

                if processing_long_comment:
                    # Look for closing */ or --]] to terminate our long comment
                    comment_pattern = r"--\]\]" if luafile else r"\*/"
                    if re.search(comment_pattern, line):
                        comments.append("*/\n")
                        processing_long_comment = False
                        processing_main_page = False
                        encounteredDoxygenCmd = False
                        continue

                    if re.search(r"\@mainpage\s", line) or re.search(r"\@page\s", line):
                        mainpage.append(line)
                        processing_main_page = True
                        encounteredDoxygenCmd = True
                        continue

                    if re.search(r"\*\s+\\par", line):       # Match * \par => Paragraph
                        encounteredDoxygenCmd = True
                        continue

                    # Check for some special custom tags...

                    #####
                    # @LUAENUM in C++ code
                    #####
                    # Check the regexes here: http://www.regexe.com
                    # Handle Lua enum defs: "@luaenum ObjType(2)" or "@luaenum ObjType(2,1,4)"  1, 2, or 3 nums are ok
                    #                                $1        $2           $4           $6
                    match = re.search(r"\@luaenum\s+(\w+)\s*\((\d+)\s*(,\s*(\d+)\s*(,\s*(\d+))?)?\s*\)", line)
                    if match:
                        collectingEnumMode = EnumMode.LUA_ENUM_COMMENT
                        enumName = match.groups()[0]
                        enumColumn = match.groups()[1]
                        descrColumn = -1 if match.groups()[3] == "" else match.groups()[3]          # Optional
                        enumIgnoreColumn = None if match.groups()[5] == "" else match.groups()[5]   # Optional
                        encounteredDoxygenCmd = True

                        enums.append(f"/**\n  * \\@defgroup {enumName}Enum {enumName}\n")

                        continue
                        # Parsing:
                        # /**
                        #   * @luaenum ClipType(1,1)
                        #   * Supported operations for clipPolygon. For a description of the operations...
                        #   */
                        # #define CLIP_TYPE_TABLE \
                        #     CLIP_TYPE_ITEM( Intersection, ClipperLib::ctIntersection ) \
                        #     CLIP_TYPE_ITEM( Union,        ClipperLib::ctUnion) \
                        #     CLIP_TYPE_ITEM( Difference,   ClipperLib::ctDifference ) \
                        #     CLIP_TYPE_ITEM( Xor,          ClipperLib::ctXor ) \


                    # Look for @geom, and replace with @par Geometry \n
                    match = re.search(r"\@geom\s+(.*)$", line)
                    if match:
                        print(f"line = {line}")
                        body = match.groups()[0]
                        print(f"body = {body}")
                        comments.append(f"\\par Geometry\n{body}\n")
                        continue

                    #####
                    # @LUAFUNCSHEADER delcaration in C++ code
                    # Look for  "* @luafuncsheader <class>" followed by a block of text.  class is the class we're documenting, obviously.
                    # This is a magic item that lets us, through extreme hackery, inject a comment at the top of the functions list (as is done with Ship)
                    # Currently only support one per file.  That should be enough.
                    match = re.search(r"^\s*\*\s*@luafuncsheader\s+(\w+)", line)
                    if match:
                        # Now we need to do something that will make it through Doxygen and emerge in a recognizable form for the postprocessor to work on
                        # We'll use a dummy function and some dummy documentation.  We'll fix it in post!
                        xclass = match.groups()[0]
                        if xclass not in classes:
                            classes[xclass] = []

                        classes[xclass].append(f"void {FUNCS_HEADER_MARKER}() {{ }}\n")

                        # And the dummy documentation -- the encounteredDoxygenCmd tells us to keep reading until we end the comment block
                        comments.append(f"\\fn {xclass}::{FUNCS_HEADER_MARKER}\n")
                        encounteredDoxygenCmd = True

                        continue

                    #####
                    # @LUAFUNC delcaration in C++ code
                    #####
                    # Look for: "* @luafunc static table Geom::triangulate(mixed polygons)"  [retval (table) and args are optional]

                    #   staticness -> "static"
                    #   voidlessRetval -> "table"
                    #   xclass -> "Geom"
                    #   method -> "triangulate"
                    #   args -> "mixed polygons"
                    match = re.search(r"^\s*\*\s*@luafunc\s+(.*)$", line)
                    if match:
                        # In C++ code, we use "::" to separate classes from functions (class::func); in Lua, we use "." or ":" (class.func).
                        sep = "[.:]" if luafile else "::"

                        #                                      $1          $2       $3                  $4    $5
                        match = re.search(r".*?@luafunc\s+(static\s+)?(\w+\s+)?(?:(\w+)" + sep + r")?(.+?)\((.*)\)", line)     # Grab retval, class, method, and args from $line

                        staticness = match.groups()[0].strip() if match.groups()[0] else ""
                        retval = match.groups()[1] if match.groups()[1] else "void"         # Retval is optional, use void if omitted
                        voidlessRetval = match.groups()[1] or ""
                        xclass  = match.groups()[2] or "global"   # If no class is given the function is assumed to be global
                        method = match.groups()[3]
                        args   = match.groups()[4]     # Args are optional

                        if not method:
                            raise Exception(f"Couldn't get method name from {line}\n")   # Must have a method; should never happen


                        # retval =~ s|\s+$||      # Trim any trailing spaces from $retval

                        # Use voidlessRetval to avoid having "void" show up where we'd rather omit the return type altogether
                        comments.append(f" \\fn {voidlessRetval} {xclass}::{method}({args})\n")

                        # Here we generate some boilerplate standard code and such
                        is_constructor = xclass == method
                        if is_constructor:  # Constructors come in the form of class::method where class and method are the same
                            comments.append(f"\\brief Constructor.\n\nExample:\n@code\n{xclass.lower()} = {xclass}.new({args})\n...\nlevelgen:addItem({xclass.lower()})\n@endcode\n\n")

                        # Find an earlier definition and delete it (if it still exists); but not if it's a constructor.
                        # This might have come from an earlier GENERATE_LUA_METHODS_TABLE block.
                        # We do this in order to provide more complete method descriptions if they are found subsequently.  I think.
                        else:
                            try:
                                if xclass in classes:
                                    classes[xclass].remove(make_method_line(method))
                            except ValueError:
                                pass    # Item is not in the list; this is fine, nothing to do.

                        # Add our new sig to the list
                        if xclass:
                            if xclass not in classes:
                                classes[xclass] = []

                            classes[xclass].append(f"{staticness} {retval} {method}({args}) {{ /* From '{line.strip()}' */ }}\n")
                        else:
                            globalfunctions.append(f"{retval} {method}({args}) {{ /* From '{line}' */ }}\n")

                        encounteredDoxygenCmd = True

                        continue


                    match = re.search(r"\@luaclass\s+(\w+)\s*$", line)        # Description of a class defined in a header file
                    if match:
                        comments.append(f" \\class {match.groups()[0]}\n")

                        encounteredDoxygenCmd = True

                        continue


                    match = re.search(r"\@luavclass\s+(\w+)\s*$", line)       # Description of a virtual class, not defined in any C++ cod
                    if match:
                        xclass = match.groups()[0]
                        comments.append(" \\class $class\n")

                        if xclass not in classes:
                            classes[xclass] = []
                        classes[xclass].append(f"class {match.groups()[0]} {{\n")
                        classes[xclass].append("public:\n")

                        encounteredDoxygenCmd = True

                        continue

                    match = re.search(r"\@descr\s+(.*)$", line)
                    if match:
                        comments.append(f"\n {match.groups()[0]}\n")
                        encounteredDoxygenCmd = True
                        continue


                    # Otherwise keep the line unaltered and put it in the appropriate array
                    if processing_main_page:
                        mainpage.append(line)
                    elif collectingEnumMode != EnumMode.NOT_COLLECTING:
                        enums.append(line)
                    elif encounteredDoxygenCmd:
                        comments.append(line)       # @code ends up here

                    continue


                # Starting with an enum def that looks like this:
                # /**
                #  * @luaenum Weapon(2[,n])  <=== 2 refers to 0-based index of column containing Lua enum name, n refers to column specifying whether to include this item
                #  * The Weapon enum can be used to represent a weapon in some functions.
                #  */
                #  #define WEAPON_ITEM_TABLE \
                #    WEAPON_ITEM(WeaponPhaser,     "Phaser",      "Phaser",     100,   500,   500,  600, 1000, 0.21f,  0,       false, ProjectilePhaser ) \
                #    WEAPON_ITEM(WeaponBounce,     "Bouncer",     "Bouncer",    100,  1800,  1800,  540, 1500, 0.15f,  0.5f,    false, ProjectileBounce ) \
                #
                #
                # Make this:
                # /** @defgroup WeaponEnum Weapon
                #  *  The Weapons enum has values for each type of weapon in Bitfighter.
                #  *  @{
                #  *  @section Weapon
                #  * __Weapon__
                #  * * %Weapon.%Phaser
                #  * * %Weapon.%Bouncer
                #  @}

                if collectingEnumMode != EnumMode.NOT_COLLECTING:
                    # If we get here we presume the @luaenum comment has been closed, and the next #define we see will begin the enum itself
                    # Enum will continue until we hit a line with no trailing \
                    match = re.search(r"#\s*define", line)
                    if match:
                        enums.append(r"\@\{\n")
                        enums.append(f"# {enumName}\n")   # Add the list header
                        collectingEnumMode = EnumMode.CPP_DEFINE
                        continue

                    if collectingEnumMode == EnumMode.LUA_ENUM_COMMENT:
                        continue     # Skip lines until we hit a #define

                    # If we're here, collectingEnumMode == EnumMode.CPP_DEFINE, and we're processing an enum definition line
                    line = re.sub(r"/\*.*?\*/", "", line)         # Remove embedded comments
                    if re.search(r"^\W*\\$", line):                # Skip any lines that have no \w chars, as long as they end in a backslash
                        continue


                    # Skip blank lines, or those that look like they are starting with a comment
                    match = re.search(r"^\s*$", line)
                    if not match:
                        match = re.search(r"^\s*//", line)
                    if not match: match = re.search(r"\s*/\*", line)

                    if match:
                        # line =~ m/[^(]+\((.+)\)/
                        # string = match.groups()[0]
                        words = re.search(r'("[^"]+"|[^,]+)(?:,\s*)?', line)
                        # ????

                        # Skip items marked as not to be shared with Lua... see #define TYPE_NUMBER_TABLE for example
                        if enumIgnoreColumn is not None and words[enumIgnoreColumn] == "false":
                            continue

                        enumDescr =  words[descrColumn] if descrColumn != -1 else ""

                        # Clean up descr -- remove leading and traling non-word characters... i.e. junk
                        enumDescr = re.sub(r'^\W*"', "", enumDescr)         # Remove leading junk
                        enumDescr = re.sub(r'"\W*$', "", enumDescr)         # Remove trailing junk


                        # Suppress any words that might trigger linking
                        enumDescr = re.sub(r'\s(\w+)', words[1], enumDescr)     # ???


                        enumval = words[enumColumn]
                        enumval = re.sub(r'[\s"\)\\]*', "", enumval)         # Strip out quotes and whitespace and other junk

                        # continue unless $enumval;      # Skip empty enumvals... should never happen, but does
                        enums.append(f" * * %{enumName}.%{enumval} <br>\n `{enumDescr}` <br>\n");    # Produces:  * * %Weapon.Triple  Triple

                        # no next here, always want to do the termination check below

                    if  re.search(r"\\\r*$", line):  # Line has no terminating \, it's the last of its kind!
                        enums.append("@}\n");       # Close doxygen group block
                        enums.append("*/\n\n");     # Close comment

                        collectingEnumMode = EnumMode.NOT_COLLECTING          # This enum is complete!


                    continue



        # If we added any lines to keepers, write it out... otherwise skip it!
        if globalfunctions or comments or classes:
            base, ext = os.path.splitext(os.path.basename(file))
            ext = ext.replace(".", "")

            # Write the simulated .h file

            outfile = os.path.join(outpath, f"{base}__{ext}.h")

            with open(outfile, "w") as filex:
                filex.write("// This file was generated automatically from the C++ source to feed doxygen.  It will be overwritten.\n\n")
                filex.write(f"// Generated {datetime.now()}\n\n")


                for key in classes:
                    filex.write("".join(classes[key]));      # Main body of class
                    filex.write(f"}}; // {key}\n")  # Close the class

                filex.write("\n\n// What follows is a dump of the globalfunctions list\n\n")
                filex.write("namespace global {\n" + "\n".join(globalfunctions) + "}\n")

                filex.write("\n\n// What follows is a dump of the comments list\n\n")
                filex.write("".join(comments))
        else:
            print("\tNothing to do")

    # Finally, write our main page data
    with open(os.path.join(outpath, "main_page_content.h"), "w") as filex:
        filex.write("// This file was generated automatically from the C++ source to feed doxygen.  It will be overwritten.\n\n")
        filex.write(f"// Generated {datetime.now()}\n\n")

        filex.write("/**\n")
        filex.write("".join(mainpage) + "\n")
        filex.write("*/\n")

        filex.write("".join(enums))


def run_doxygen():
    os.chdir("doc")
    subprocess.run(f"{doxygen_cmd} luadocs.doxygen")
    os.chdir("..")


def post_process():
    """ Post-process the generated doxygen stuff """

    print("Fixing doxygen output...")

    os.chdir("doc")

    files = glob("./html/class_*.html")

    for file in files:
        print(".", end="", flush=True)
        cleaned_html = ""

        with open(file, "r") as infile:

            # Do some quick text cleanup as we read the file, but before we feed it to etree
            for line in infile:
                cleaned_html += cleanup_html(line)


        # Do some fancier parsing with something that understands the document structure
        root = etree.fromstring(cleaned_html)

        ns = {"x": "http://www.w3.org/1999/xhtml"}      # Namespace dict

        # Remove first two annoying "More..." links...
        elements = root.xpath("//x:a[text()='More...']", namespaces=ns)
        for element in elements[:2]:
            element.getparent().remove(element)

        # Remove Public (it's confusing!)
        replace_text(root, "Public Member Function", "Member Function")
        replace_text(root, "More...", "[details]")


        elements_to_delete = []

        # Find rows in our Member Functions table that refer to the DummyConstructor
        # Looking for rows in tables of class memberdelcs that contain a td that contains a link for DummyConstructor
        elements = root.xpath(f"//x:table[@class='memberdecls']//x:tr[descendant::x:td/x:a[contains(text(),'{FUNCS_HEADER_MARKER}')]]", namespaces=ns)
        if elements:
            elements_to_delete.append(elements[0])
            # <tr xmlns="http://www.w3.org/1999/xhtml" class="memitem:a515b33956a05bb5a042488cf4f361019">
            #   <td class="memItemLeft" align="right" valign="top">void&#160;</td>
            #   <td class="memItemRight" valign="bottom"><a class="el" href="class_ship.html#a515b33956a05bb5a042488cf4f361019">DummyConstructor</a> ()</td>
            # </tr>

        # Looking for rows in tables of class memberdecls that have a immediately preceding row that contains a td with a link for DummyConstructor
        # This should find rows immediately following the rows in rows_to_modify
        elements = root.xpath(f"//x:table[@class='memberdecls']//x:tr[preceding::x:tr[1][descendant::x:td/x:a[contains(text(),'{FUNCS_HEADER_MARKER}')]]]", namespaces=ns)
        if elements:
            elements_to_delete.append(elements[0])

        elements = root.xpath(f"//x:h2[@class='memtitle' and contains(text(), '{FUNCS_HEADER_MARKER}')]", namespaces=ns)
        if elements:
            elements_to_delete.append(elements[0])
            # <h2 class="memtitle">
            #   <span class="permalink"><a href="#a515b33956a05bb5a042488cf4f361019">&#9670;&#160;</a></span> DummyConstructor()
            # </h2>

        elements = root.xpath(f"//x:div[preceding::x:h2[@class='memtitle' and contains(text(), '{FUNCS_HEADER_MARKER}')]]", namespaces=ns)
        if elements:
            elements_to_delete.append(elements[0])
            # The div following the one above


        # Retrieve our description, which is down in the description of DummyConstructor
        elements = root.xpath(f"//x:div[preceding::x:td[contains(text(),'Ship::DummyConstructor')]]/child::*", namespaces=ns)
        if elements:
            new_content = etree.tostring(elements[0]).decode("utf-8")

            parent = root.xpath(f"//x:table[@class='memberdecls']", namespaces=ns)[0]
            new_elements = [
                etree.fromstring(f'<tr><td colspan="2" class="memItemRight">{new_content}</td></tr>'),
                etree.fromstring(f'<tr><td class="memSeparator" colspan="2">&#160;</td></tr>'),
            ]

            new_elements.reverse()
            for new_element in new_elements:
                parent.insert(1, new_element)


        class_urls = get_class_urls(root, ns)

        move_class_names_to_inherited_tag(root, ns, class_urls)
        clean_up_method_sigs(root, ns)


        # Delete any items we've marked for deletion
        for element in elements_to_delete:
            # print("deleting", etree.tostring(element, pretty_print=True).decode("utf-8"))
            delete_node(element)


        with open(file, "w") as outfile:
            outfile.write(etree.tostring(root, method="html").decode("utf-8"))


def delete_node(element):
    element.getparent().remove(element)


def move_class_names_to_inherited_tag(root: Any, ns: Dict[str, str], class_urls: Dict[str, str]) -> None:
    """ Move class names to inherited tag; this does not capture all of our classes, only the inherited ones. """
    tables = root.xpath("//x:table[contains(.,'inherited')]", namespaces=ns)     # Matches entire table below
    # <table class="mlabels">
    #   <tr>
    #     <td class="mlabels-left">
    #         <table class="memname">
    #           <tr>
    #             <td class="memname">BfObject::setGeom </td>                         <=== Move BfObject from here...
    #             <td>(</td>
    #             <td class="paramtype"><a class="el" href="class_geom.html">Geom</a></td>
    #             <td class="paramname"><em>geometry</em></td>
    #             <td>)</td>
    #             <td></td>
    #           </tr>
    #         </table>
    #     </td>
    #     <td class="mlabels-right">
    #         <span class="mlabels"><span class="mlabel">inherited</span></span>      <=== ...to here
    #     </td>
    #   </tr>
    # </table>

    for table in tables:
        memnames = table.xpath(".//x:td[@class='memname']/text()", namespaces=ns)
        if not memnames:
            continue
        assert len(memnames) == 1

        parts = parse_member_name(memnames[0])

        if not parts:
            continue

        ret_type, xclass, fn = parts


        inherited_elements = table.xpath(".//x:span[@class='mlabel' and text()='inherited']", namespaces=ns)
        if inherited_elements:
            assert len(inherited_elements) == 1
            # inherited_elements[0].text = f"inherited from {xclass}"

            html = f'inherited from {xclass}'
            if xclass in class_urls:        # Use the URL if we have one
                html = f'<a href="{class_urls[xclass]}">{html}</a>'
            inherited_from = etree.fromstring(html)

            inherited_elements[0].clear()
            inherited_elements[0].insert(1, inherited_from)


def parse_member_name(memname: str) -> Optional[Tuple[str, str, str]]:
    """
    Given a string like "int BFObject::doMath", return ["int", "BfObject", "doMath"].
    Some parts may be missing; if passed string does not contain "::", bail and return None.
    """
    if "::" not in memname:    # Not sure this check is necessary
        return None

    xclass, fn = memname.split("::")

    if " " in xclass:
        ret_type, xclass = xclass.split(" ")
    else:
        ret_type = ""

    return ret_type, xclass, fn


def clean_up_method_sigs(root: Any, ns: Dict[str, str]) -> None:
    # Spiff up method signatures (looking for inner tables found above, but this time even ones without adjacent inherited tags)
    tables = root.xpath("//x:table[@class='memname']", namespaces=ns)
    # <table class="memname">
    #   <tr>
    #     <td class="memname">BfObject::setGeom </td>                       <=== "BfObject::setGeom" to "setGeom"
    #     <td>(</td>
    #     <td class="paramtype"><a class="el" href="class_geom.html">Geom</a></td>
    #     <td class="paramname"><em>geometry</em></td>
    #     <td>)</td>
    #     <td></td>                                                         <=== Add "-> <return type>" to this cell
    #   </tr>
    # </table>

    for table in tables:
        memnames = table.xpath(".//x:td[@class='memname']/text()", namespaces=ns)

        parts = parse_member_name(memnames[0])

        if not parts:
            continue

        ret_type, xclass, function_name = parts

        # table.xpath(".//x:td[@class='memname']", namespaces=ns)[0].text = function_name    # Remove class and return
        cells = table.xpath(".//x:td", namespaces=ns)
        cells[0].clear()
        cells[0].text = function_name
        # cells[-1].text = f"-> {ret_type if ret_type else 'nil'}"      # Add return type to end of row

        param_types = table.xpath(".//x:td[@class='paramtype']", namespaces=ns)
        param_names = table.xpath(".//x:td[@class='paramname']", namespaces=ns)

        # These lists will be imbalanced if there are no args... for some reason doxygen inserts an empty
        # <td class="paramname"></td> tag when there are no args, but does not also include it's corresponding
        # <td class="paramtype"></td>.
        if len(param_types) == len(param_names):
            argstrs = []
            for i in range(len(param_types)):
                # Use itertext() to burrow into any inner tags and grab all the text
                param_name = "".join(param_names[i].itertext()).replace(",", "")
                param_type = "".join(param_types[i].itertext()).replace(",", "")
                argstrs.append(f'<span class="paramname">{param_name}</span>: <span class="paramtype">{param_type}</span>')

                delete_node(param_types[i])     # Won't be needing this!

            # The argline styles are defined in luadocs_html_extra_stylesheet.css
            new_row = etree.fromstring(f"""
                <tr class="nofloat argline">
                    <td colspan="{len(cells)}">
                        <span class="argtypes">Arg types:</span>
                        {", ".join(argstrs)}{NBSP * 2}|{NBSP * 2}returns <span class="returntype">{ret_type if ret_type else 'nil'}</span>
                    </td>
                </tr>
            """)
            table.append(new_row)


# https://stackoverflow.com/questions/65506059/how-can-i-get-the-text-from-this-html-snippet-using-lxml
def replace_text(root: Any, search_str: str, replace_str: str):
    context = etree.iterwalk(root, events=("start", "end"))
    for action, elem in context:
        if elem.text and search_str in elem.text:
            elem.text = elem.text.replace(search_str, replace_str)
        elif elem.tail and search_str in elem.tail:
            elem.tail = elem.tail.replace(search_str, replace_str)


def get_class_urls(root: Any, ns: Dict[str, str]) -> Dict[str, str]:
    """
    Build a list of URLs for each parent class. These are convenitely available in the
    map associated with the class hiearchy at the top of each page.
    """
    areas = root.xpath("//x:map/x:area", namespaces=ns)
    # <map id="Ship_map" name="Ship_map">
    #   <area href="class_move_object.html" title="Parent class of most things that move (except bullets)." alt="MoveObject" shape="rect" coords="0,112,81,136">
    #   <area href="class_item.html" title="Parent class for most common game items." alt="Item" shape="rect" coords="0,56,81,80">
    #   <area href="class_bf_object.html" alt="BfObject" shape="rect" coords="0,0,81,24">
    #   <area href="class_robot.html" alt="Robot" shape="rect" coords="0,224,81,248">
    # </map>
    class_urls = {}
    for area in areas:
        class_urls[area.get("alt")] = area.get("href")

    return class_urls


def cleanup_html(line: str) -> str:
    """
    These things seem to anger lxml for some reason... let's make it happy.
    These commands are run on the raw file, before lxml starts parsing.
    """
    # Replace these with their equivalents
    line = line.replace("&nbsp;", NBSP)
    line = line.replace("&ndash;", "–")

    # Remove the offending &nbsp that makes some )s appear in the wrong place
    line = re.sub(r'(<td class="paramtype">.+)&#160;(</td>)', r"\1\2", line)        # &#160; is a nobsp char

    line = re.sub(r"/* @license.*?\*/", "", line)       # These comments cause problems for some reason

    return line



if __name__ == "__main__":
    main()