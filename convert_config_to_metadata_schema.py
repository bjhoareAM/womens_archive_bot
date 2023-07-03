import json
import yaml
import sys # Read CLI arguments

# ----------------
# Configuration settings
# ----------------

# Set default values
config_path = 'config.yaml'
out_file_path = 'csv-metadata.json'
default_language = 'en'
node_root_url= 'http://example.com/.well-known/genid/'

arg_vals = sys.argv[1:]
# see https://www.gnu.org/prep/standards/html_node/_002d_002dversion.html
if '--version' in arg_vals or '-V' in arg_vals: # provide version information according to GNU standards 
    print('Revision date:', created)
    sys.exit()

if '--help' in arg_vals or '-H' in arg_vals: # provide help information according to GNU standards
    # needs to be expanded to include brief info on invoking the program
    print('For help, see the documentation page at https://github.com/HeardLibrary/linked-data/blob/master/vanderbot/convert-config.md')
    print('Report bugs to: steve.baskauf@vanderbilt.edu')
    sys.exit()

# Code from https://realpython.com/python-command-line-arguments/#a-few-methods-for-parsing-python-command-line-arguments
opts = [opt for opt in arg_vals if opt.startswith('-')]
args = [arg for arg in arg_vals if not arg.startswith('-')]

if '--config' in opts: #  set path to configuration file
    config_path = args[opts.index('--config')]
if '-C' in opts: 
    config_path = args[opts.index('-C')]

if '--meta' in opts: #  set path to output metadata description file
    out_file_path = args[opts.index('--meta')]
if '-M' in opts: 
    out_file_path = args[opts.index('-M')]

if '--lang' in opts: #  set default language for labels in columns whose output is suppressed
    default_language = args[opts.index('--lang')]
if '-L' in opts: 
    default_language = args[opts.index('-L')]

values_structures = {
    'date': [
        {
        'suffix': '_val',
        'datatype': 'dateTime',
        'prop_localname': 'timeValue',
        'item_value': False
        },
        {
        'suffix': '_prec',
        'datatype': 'integer',
        'prop_localname': 'timePrecision',
        'item_value': False
        }
    ],
    'quantity': [
        {
        'suffix': '_val',
        'datatype': 'decimal',
        'prop_localname': 'quantityAmount',
        'item_value': False
        },
        {
        'suffix': '_unit',
        'datatype': 'string',
        'prop_localname': 'quantityUnit',
        'item_value': True
        }
    ],
    'globecoordinate': [
        {
        'suffix': '_val',
        'datatype': 'float',
        'prop_localname': 'geoLatitude',
        'item_value': False
        },
        {
        'suffix': '_long',
        'datatype': 'float',
        'prop_localname': 'geoLongitude',
        'item_value': False
        },
        {
        'suffix': '_prec',
        'datatype': 'float',
        'prop_localname': 'geoPrecision',
        'item_value': False
        }
    ]
}

triple_structures = {
    'string': {
        'type': 'string',
        'iri_stem': '',
        'lang_value': False
    },
    'item': {
        'type': 'item',
        'iri_stem': 'http://www.wikidata.org/entity/{',
        'lang_value': False
    },
    'uri': {
        'type': 'iri',
        'iri_stem': '{+',
        'lang_value': False
    },
    'monolingualtext': {
        'type': 'string',
        'iri_stem': '',
        'lang_value': True
    },
    'date': {
        'type': 'node',
        'iri_stem': 'http://example.com/.well-known/genid/{',
        'lang_value': False
    },
    'quantity': {
        'type': 'node',
        'iri_stem': 'http://example.com/.well-known/genid/{',
        'lang_value': False
    },
    'globecoordinate': {
        'type': 'node',
        'iri_stem': 'http://example.com/.well-known/genid/{',
        'lang_value': False
    }    
}

def built_triple(struct, triple_structure, subject_column, prop, triple_type, column_name, lang, header_row):
    dic = {}
    if triple_structure['type'] == 'node':
        column_name += '_nodeId'
    dic['titles'] = column_name
    header_row += dic['titles'] + ','
    dic['name'] = column_name
    dic['datatype'] = 'string'
    if triple_type == 'reference':
        dic['aboutUrl'] = 'http://www.wikidata.org/reference/{' + subject_column + '_hash}'
    else:
        dic['aboutUrl'] = 'http://www.wikidata.org/entity/statement/{qid}-{' + subject_column + '_uuid}'
    prop_url = 'http://www.wikidata.org/prop/' + triple_type + '/'
    if triple_structure['type'] == 'node':
        prop_url += 'value/'
    dic['propertyUrl'] = prop_url + prop
    if triple_structure['iri_stem'] != '':
        dic['valueUrl'] = triple_structure['iri_stem'] + column_name + '}'
    if triple_structure['lang_value']:
        dic['lang'] = lang
    struct.append(dic)
    return(struct, header_row)        

def build_value_node(column_list, value_structures, column_name, header_row):
    for node_prop in value_structures:
        dic = {}
        dic['titles'] = column_name + node_prop['suffix']
        header_row += dic['titles'] + ','
        dic['name'] = column_name + node_prop['suffix']
        dic['datatype'] = node_prop['datatype']
        dic['aboutUrl'] = node_root_url + '{' + column_name + '_nodeId}'
        dic['propertyUrl'] = 'http://wikiba.se/ontology#' + node_prop['prop_localname']
        if node_prop['item_value']:
            dic['valueUrl'] = 'http://www.wikidata.org/entity/{' + column_name + node_prop['suffix'] + '}'
        column_list.append(dic)
    return(column_list, header_row)

def build_statement(column_list, statement_data, header_row):
    if 'language' in statement_data:
        lang = statement_data['language']
    else:
        lang = ''
    value_type = statement_data['value_type']
    prop = statement_data['pid']
    column_name = statement_data['variable']
    
    # Build the triple from subject to statement node
    dic = {}
    dic['titles'] = column_name + '_uuid'
    header_row += dic['titles'] + ','
    dic['name'] = column_name + '_uuid'
    dic['datatype'] = 'string'
    dic['aboutUrl'] = 'http://www.wikidata.org/entity/{qid}'
    dic['propertyUrl'] = 'http://www.wikidata.org/prop/' + prop
    dic['valueUrl'] = 'http://www.wikidata.org/entity/statement/{qid}-{' + column_name + '_uuid}'
    column_list.append(dic)

    # Build the triple from the statement node to the value
    column_list, header_row = built_triple(column_list, triple_structures[value_type], statement_data['variable'], prop, 'statement', column_name, lang, header_row)
    
    # Build any value node triples
    if triple_structures[value_type]['type'] == 'node':
        column_list, header_row = build_value_node(column_list, values_structures[value_type], column_name, header_row)
    
    # Build qualifier triples
    column_list, header_row = build_qualifiers(column_list, column_name, statement_data['qual'], header_row)
    
    # Build reference triples
    if len(statement_data['ref']) > 0:
        column_list, header_row = build_references(column_list, column_name, statement_data['ref'], header_row)
    
    return column_list, header_row

def build_references(column_list, subject_name, references_data, header_row):

    # Build the triple from statement to the reference node
    dic = {}
    dic['titles'] = subject_name + '_ref1_hash'
    header_row += dic['titles'] + ','
    dic['name'] = subject_name + '_ref1_hash'
    dic['datatype'] = 'string'
    dic['aboutUrl'] = 'http://www.wikidata.org/entity/statement/{qid}-{' + subject_name + '_uuid}'
    dic['propertyUrl'] = 'prov:wasDerivedFrom'
    dic['valueUrl'] = 'http://www.wikidata.org/reference/{' + subject_name + '_ref1_hash}'
    column_list.append(dic)        

    for reference_data in references_data:
        if 'language' in reference_data:
            lang = reference_data['language']
        else:
            lang = ''
        value_type = reference_data['value_type']
        prop = reference_data['pid']
        column_name = reference_data['variable']
        
        # Build the triple from the reference node to the value
        column_list, header_row = built_triple(column_list, triple_structures[value_type], subject_name + '_ref1', prop, 'reference', subject_name + '_ref1_' + column_name, lang, header_row)

        # Build any value node triples
        if triple_structures[value_type]['type'] == 'node':
            column_list, header_row = build_value_node(column_list, values_structures[value_type], subject_name + '_ref1_' + column_name, header_row)

    return column_list, header_row

def build_qualifiers(column_list, subject_name, qualifiers_data, header_row):
    for qualifier_data in qualifiers_data:
        if 'language' in qualifier_data:
            lang = qualifier_data['language']
        else:
            lang = ''
        value_type = qualifier_data['value_type']
        prop = qualifier_data['pid']
        column_name = qualifier_data['variable']

        # Build the triple from the statement node to the qualifier value
        column_list, header_row = built_triple(column_list, triple_structures[value_type], subject_name, prop, 'qualifier', subject_name + '_' + column_name, lang, header_row)

        # Build any value node triples
        if triple_structures[value_type]['type'] == 'node':
            column_list, header_row = build_value_node(column_list, values_structures[value_type], subject_name + '_' + column_name, header_row)

    return column_list, header_row

def build_label_description(language, kind, header_row):
    dic = {}
    dic['titles'] = kind + '_' + language.replace('-', '_')
    header_row += dic['titles'] + ','
    dic['name'] = kind + '_' + language.replace('-', '_')
    dic['datatype'] = 'string'
    dic['aboutUrl'] = 'http://www.wikidata.org/entity/{qid}'
    if kind == 'label':
        dic['propertyUrl'] = 'rdfs:label'
    else:
        dic['propertyUrl'] = 'schema:description'
    dic['lang'] = language
    return dic, header_row

def build_table(data_path, outfile):
    table = {}
    table['url'] = outfile['output_file_name']
    column_list = [
        {
            'titles': 'qid',
            'name': 'qid',
            'datatype': 'string',
            'suppressOutput': True
        }
    ]
    header_row = 'qid,'

    if 'ignore' in outfile:
        for ignore_column_name in outfile['ignore']:
            ignore_column = {
                'titles': ignore_column_name,
                'name': ignore_column_name,
                'datatype': 'string',
                'suppressOutput': True
            }
            column_list.append(ignore_column)
            header_row += ignore_column_name + ','
    
    if outfile['manage_descriptions']:
        for language in outfile['label_description_language_list']:
            dic, header_row = build_label_description(language, 'label', header_row)
            column_list.append(dic)
        for language in outfile['label_description_language_list']:
            dic, header_row = build_label_description(language, 'description', header_row)
            column_list.append(dic)
    else:
        label_column = {
            'titles': 'label_' + default_language,
            'name': 'label_' + default_language,
            'datatype': 'string',
            'suppressOutput': True
        }
        column_list.append(label_column)
        header_row += 'label_' + default_language + ','
    
    for statement_data in outfile['prop_list']:
        column_list, header_row = build_statement(column_list, statement_data, header_row)
    table_schema = {}
    table_schema['columns'] = column_list
    table['tableSchema'] = table_schema

    # remove trailing comma from header row string and add newline
    header_row = header_row[:len(header_row)-1] + '\n'

    # Create the CSV associated with the schema, header row only
    with open(data_path + 'h' + outfile['output_file_name'], 'wt', encoding='utf-8') as file_object: # prepend "h" to avoid overwriting existing data
        file_object.write(header_row)
    return table

# ----------------
# Beginning of main script
# ----------------

# In the case where no --config option is specified, the default config.yaml will be opened.
# If this fails, try opening the old default, config.json
try:
    with open(config_path, 'r') as file_object:
        config = yaml.safe_load(file_object)
except:
    with open('config.json', 'r') as file_object:
        config = yaml.safe_load(file_object)


data_path = config['data_path']
#item_source_csv = config['item_source_csv'] 
#item_query_pattern_file = config['item_pattern_file']
outfiles = config['outfiles']

csv_metadata = {}
csv_metadata['@type'] = 'TableGroup'
csv_metadata['@context'] = 'http://www.w3.org/ns/csvw'

tables = []
for outfile in outfiles:
    table = build_table(data_path, outfile)
    tables.append(table)
    
csv_metadata['tables'] = tables

out_text = json.dumps(csv_metadata, indent = 2)
#print(out_text)

with open(data_path + out_file_path, 'wt', encoding='utf-8') as file_object:
    file_object.write(out_text)
