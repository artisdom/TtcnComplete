import re
import logging
import os
import subprocess
import json
import sys

#logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', level=logging.DEBUG)

class CompleteDictGenerator(object):
    """docstring for CompleteDictGenerator"""
    completion_result = None
    file_name = None
    file_context = None
    import_modules = None
    root_path = None
    tags_file_context = []
    find_type = None

    def __init__(self, file_name, root_path, type_name = None):
        self.file_name = file_name
        self.root_path = root_path
        self.type_name = type_name
        print("root_path", root_path)
        print("file_name", file_name)
        print("................", os.path.join(root_path, file_name))
        with open(os.path.join(root_path, file_name), 'r') as f:
            self.file_context = f.readlines()

        self.completion_result = dict(modulename=file_name)
        self.import_modules = CompleteDictGenerator._get_import_module(self.file_context)
        self.import_modules.append(os.path.basename(self.file_name).split('.')[0])

        with open(os.path.join(root_path, 'test.tags'), 'r+') as fo:
            self.tags_file_context = fo.readlines()

        self.find_type = False
        

    @staticmethod
    def _get_module_name_for_tags_file(tags_file_context, type_name):
        #fo = open(tags_file, 'r+')
        type_pattern = '\s*%s\s+([\w/\.]+)' % type_name
        #file_context = fo.readlines()
        res = []
        for line in tags_file_context:
            m = re.match(type_pattern,line)
            if m:
                res.append( m.group(1))
        return res

    def parse_type(self):
        if self.type_name:
            type_pattern = '^\s*type\s+(record|union|set)\s+(%s)' % self.type_name
        else:
            type_pattern = '^\s*type\s+(record|union|set)\s+(\w+)'
        list_pattern = '^\s*type\s+(record|set)\s+(of|length)'
        i = 0
        while i < len(self.file_context):
            if re.match(list_pattern, self.file_context[i]):
                i += 1
                continue
            m = re.match(type_pattern, self.file_context[i])
            if m:
                logging.debug("type start at: %s", self.file_context[i])
                parent_type_name = m.group(2)
                logging.debug("parent type name is %s", parent_type_name)
                logging.info(" get sublist for type %s", parent_type_name)
                subtype_pattern = re.compile('^\s*({)?\s+(\w+)\s+(\w+)')
                i += 1
                if re.match('{', self.file_context[i]):
                    #skip single line {
                    i += 1
                subtype_list = []
                while i < len(self.file_context):
                    m = re.match(subtype_pattern, self.file_context[i])
                    if m:
                        self.find_type = True
                        logging.debug(" line is %s", self.file_context[i])
                        sub_type_name = m.group(2)
                        sub_variable_name = m.group(3)
                        logging.debug(" sub_type_name is %s, sub_variable_name is %s", sub_type_name, sub_variable_name)
                        tags_moudles = CompleteDictGenerator._get_module_name_for_tags_file(self.tags_file_context, sub_type_name)
                        module = CompleteDictGenerator._check_type_from_module(self.import_modules, 
                                                         tags_moudles)
                        logging.debug(" module name for type %s is %s", sub_type_name, module)

                        subtype_list.append( dict(module_name=module, 
                                            type_name=sub_type_name, 
                                            variable_name = sub_variable_name))
                    #match the end of this record
                    m = re.match('\s*}\s*', self.file_context[i])
                    if m:
                        logging.debug(" at the end of type %s", parent_type_name)
                        self.completion_result[parent_type_name] = subtype_list
                        if self.type_name:
                            return
                        else:
                            break
                    i += 1
            i += 1

    @staticmethod
    def _find(name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    @staticmethod
    def _check_type_from_module(import_modules, tags_moudles):
        for tags_module in tags_moudles:
            for import_module in import_modules:
                if import_module == os.path.basename(tags_module).split('.')[0]:
                    return tags_module
        return

    @staticmethod
    def _get_import_module(file_context):
        import_pattern = re.compile('\s*import\s*from\s*(\w+)')
        import_modules = []
        for line in file_context:
            m = re.match(import_pattern, line)
            if m:
                logging.debug(" import module: %s", m.group(1))
                import_modules.append(m.group(1))
        return import_modules

    def output_to_file(self):
        if self.find_type:
            file_name = os.path.basename(self.file_name).split('.')[0]
            output_path = os.path.join(self.root_path + '/run/completionsdict', file_name)
            fo = open(output_path, 'w+')
            json.dump(self.completion_result, fo)
            fo.close()
            logging.info("completion dict write to file %s", output_path)
            logging.info("finish to generate completion dict for file %s", file)


def find(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.ttcn'):
                file_list.append(os.path.join(root, file))
    return file_list

if __name__ == '__main__':

    c = CompleteDictGenerator("ttcn3libs\\ttcn\\GtpV2MessagesCore7.ttcn", 
                              "D:\\userdata\\humi\\My Documents\\work\SourceCode\\TTCN3_tester\\trunk\\MME_SGSN_tester\\",
                              "CreateSessionRequest")
    logging.info("start to generate completion dict for file")
    c.parse_type()
    print(c.completion_result)
    #c.output_to_file()