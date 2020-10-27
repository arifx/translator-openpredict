import logging
import pkg_resources
import uuid 
import os
from datetime import datetime
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import RDFS, XSD, DC, DCTERMS, VOID
from SPARQLWrapper import SPARQLWrapper, POST, JSON

TTL_METADATA_FILE = pkg_resources.resource_filename('openpredict', 'data/openpredict-metadata.ttl')
OPENPREDICT_NAMESPACE = 'https://w3id.org/openpredict/'

RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
SCHEMA = Namespace("http://schema.org/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
PROV = Namespace("http://www.w3.org/ns/prov#")
MLS = Namespace("http://www.w3.org/ns/mls#")
BIOLINK = Namespace("https://w3.org/biolink/")
OPENPREDICT = Namespace("https://w3id.org/openpredict/")

SPARQL_ENDPOINT_URL = 'https://graphdb.dumontierlab.com/repositories/translator-openpredict'
SPARQL_ENDPOINT_UPDATE_URL = 'https://graphdb.dumontierlab.com/repositories/translator-openpredict/statements'
SPARQL_ENDPOINT_USERNAME = os.getenv('OPENPREDICT_USERNAME')
SPARQL_ENDPOINT_PASSWORD = os.environ.get('OPENPREDICT_PASSWORD')

def insert_graph_in_sparql_endpoint(g):
    """Insert rdflib graph in a SPARQL endpoint using SPARQLWrapper

    :param g: rdflib graph to insert
    :return: SPARQL update query result
    """
    sparql = SPARQLWrapper(SPARQL_ENDPOINT_UPDATE_URL)
    sparql.setMethod(POST)
    # sparql.setHTTPAuth(BASIC)
    sparql.setCredentials(SPARQL_ENDPOINT_USERNAME, SPARQL_ENDPOINT_PASSWORD)
    query = """INSERT DATA {{ GRAPH  <https://w3id.org/openpredict/graph>
    {{
    {ntriples}
    }}
    }}
    """.format(ntriples=g.serialize(format='nt').decode('utf-8'))

    sparql.setQuery(query)
    return sparql.query()

def query_sparql_endpoint(query):
    sparql = SPARQLWrapper(SPARQL_ENDPOINT_URL)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def add_feature_metadata(id, description, type):
    """Generate RDF metadata for a feature

    :param id: if used to identify the feature
    :param description: feature description
    :param type: feature type
    :return: rdflib graph after loading the feature
    """
    g = Graph()

    feature_uri = URIRef(OPENPREDICT_NAMESPACE + 'feature/' + id)
    g.add((feature_uri, RDF.type, MLS['Feature']))
    g.add((feature_uri, DC.identifier, Literal(id)))
    g.add((feature_uri, DC.description, Literal(description)))
    g.add((feature_uri, OPENPREDICT['embedding_type'], Literal(type)))

    insert_graph_in_sparql_endpoint(g)
    return g


def add_run_metadata(scores, model_features, hyper_params):
    """Generate RDF metadata for a classifier and save it in data/openpredict-metadata.ttl, based on OpenPredict model:
    https://github.com/fair-workflows/openpredict/blob/master/data/rdf/results_disjoint_lr.nq

    :param scores: scores
    :param model_features: List of features in the model
    :param label: label of the classifier
    :return: predictions in array of JSON object
    """

    run_id = str(uuid.uuid1())
    g = Graph()
    # g.parse(TTL_METADATA_FILE, format="ttl")

    run_uri = URIRef(OPENPREDICT_NAMESPACE + 'run/' + run_id)
    run_prop_prefix = OPENPREDICT_NAMESPACE + run_id + "/"
    evaluation_uri = URIRef(OPENPREDICT_NAMESPACE + 'run/' + run_id + '/ModelEvaluation')
    # The same for all run:
    implementation_uri = URIRef(OPENPREDICT_NAMESPACE + 'implementation/OpenPredict')

    # Add Run metadata
    g.add((run_uri, RDF.type, MLS['Run']))
    g.add((run_uri, PROV['generatedAtTime'], Literal(datetime.now(), datatype=XSD.dateTime)))
    g.add((run_uri, MLS['realizes'], OPENPREDICT['LogisticRegression']))
    g.add((run_uri, MLS['executes'], implementation_uri))
    g.add((run_uri, MLS['hasOutput'], evaluation_uri))
    g.add((run_uri, MLS['hasOutput'], URIRef(run_prop_prefix + 'Model')))

    # Add Model, should we point it to the generated model?
    g.add((URIRef(run_prop_prefix + 'Model'), RDF.type, MLS['Model']))

    # Add implementation metadata
    g.add((OPENPREDICT['LogisticRegression'], RDF.type, MLS['Algorithm']))
    g.add((implementation_uri, RDF.type, MLS['Implementation']))
    g.add((implementation_uri, MLS['implements'], OPENPREDICT['LogisticRegression']))

    # Add HyperParameters and their settings to implementation
    for hyperparam, hyperparam_setting in hyper_params.items():
        hyperparam_uri = URIRef(OPENPREDICT_NAMESPACE + 'HyperParameter/' + hyperparam)
        g.add((implementation_uri, MLS['hasHyperParameter'], hyperparam_uri))
        g.add((hyperparam_uri, RDF.type, MLS['HyperParameter']))
        g.add((hyperparam_uri, RDFS.label, Literal(hyperparam)))

        hyperparam_setting_uri = URIRef(OPENPREDICT_NAMESPACE + 'HyperParameterSetting/' + hyperparam)
        g.add((implementation_uri, MLS['hasHyperParameter'], hyperparam_setting_uri))
        g.add((hyperparam_setting_uri, RDF.type, MLS['HyperParameterSetting']))
        g.add((hyperparam_setting_uri, MLS['specifiedBy'], hyperparam_uri))
        g.add((hyperparam_setting_uri, MLS['hasValue'], Literal(hyperparam_setting)))
        g.add((run_uri, MLS['hasInput'], hyperparam_setting_uri))
    
    # TODO: improve how we retrieve features
    for feature in model_features:
        feature_uri = URIRef(OPENPREDICT_NAMESPACE + 'feature/' + feature)
        # g.add((run_uri, OPENPREDICT['has_features'], feature_uri))
        g.add((run_uri, MLS['hasInput'], feature_uri))

    # Add scores as EvaluationMeasures
    g.add((evaluation_uri, RDF.type, MLS['ModelEvaluation']))
    for key in scores.keys():
        key_uri = URIRef(run_prop_prefix + key)
        g.add((evaluation_uri, MLS['specifiedBy'], key_uri))
        g.add((key_uri, RDF.type, MLS['EvaluationMeasure']))
        g.add((key_uri, RDFS.label, Literal(key)))
        g.add((key_uri, MLS['hasValue'], Literal(scores[key], datatype=XSD.double)))
        # TODO: The example puts hasValue in the ModelEvaluation
        # but that prevents to provide multiple values for 1 evaluation
        # http://ml-schema.github.io/documentation/ML%20Schema.html#overview

    insert_graph_in_sparql_endpoint(g)
    return g


def retrieve_features(type='All'):
    """Get features in the ML model
    
    :param type: type of the feature (All, Both, Drug, Disease)
    :return: JSON with features
    """
    type_filter = ''
    if (type != "All"):
        type_filter = 'FILTER(?embeddingType = "' + type + '")'

    query = """SELECT DISTINCT ?id ?description ?embeddingType
        WHERE {{
            ?feature a <http://www.w3.org/ns/mls#Feature> ;
                <http://purl.org/dc/elements/1.1/identifier> ?id ;
                <https://w3id.org/openpredict/embedding_type> ?embeddingType ;
                <http://purl.org/dc/elements/1.1/description> ?description .
            {type_filter}
        }}
        """.format(type_filter=type_filter)

    results = query_sparql_endpoint(query)

    features_json = {}
    for result in results:
        features_json[result['id']['value']] = {
            "description": result['description']['value'],
            "type": result['embeddingType']['value']
        }
    return features_json


def retrieve_models():
    """Get models with their scores and features
    
    :return: JSON with models and features
    """
    sparql_get_scores = """PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX mls: <http://www.w3.org/ns/mls#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX openpredict: <https://w3id.org/openpredict/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT DISTINCT ?run ?generatedAtTime ?featureId ?accuracy ?average_precision ?f1 ?precision ?recall ?roc_auc
        WHERE {
    		?run a mls:Run ;
           		prov:generatedAtTime ?generatedAtTime ;
                mls:hasInput ?features ;
            	mls:hasOutput ?evaluation .
            ?evaluation a mls:ModelEvaluation  .
            ?features dc:identifier ?featureId .
    
            ?evaluation mls:specifiedBy [a mls:EvaluationMeasure ; 
                        rdfs:label "accuracy" ;
                        mls:hasValue ?accuracy ] .
            ?evaluation mls:specifiedBy [ a mls:EvaluationMeasure ; 
                    rdfs:label "precision" ;
                    mls:hasValue ?precision ] .
            ?evaluation mls:specifiedBy [ a mls:EvaluationMeasure ; 
                    rdfs:label "f1" ;
                    mls:hasValue ?f1 ] .
            ?evaluation mls:specifiedBy [ a mls:EvaluationMeasure ; 
                    rdfs:label "recall" ;
                    mls:hasValue ?recall ] .
            ?evaluation mls:specifiedBy [ a mls:EvaluationMeasure ; 
                    rdfs:label "roc_auc" ;
                    mls:hasValue ?roc_auc ] .
            ?evaluation mls:specifiedBy [ a mls:EvaluationMeasure ; 
                    rdfs:label "average_precision" ;
                    mls:hasValue ?average_precision ] .
        }
        """

    results = query_sparql_endpoint(sparql_get_scores)
    features_json = {}
    for result in results:
        if result['run']['value'] in features_json:
            features_json[result['run']['value']]['features'].append(result['featureId']['value'])
        else:
            features_json[result['run']['value']] = {
                "generatedAtTime": result['generatedAtTime']['value'],
                'features': [result['featureId']['value']],
                'accuracy': result['accuracy']['value'],
                'average_precision': result['average_precision']['value'],
                'f1': result['f1']['value'],
                'precision': result['precision']['value'],
                'recall': result['recall']['value'],
                'roc_auc': result['roc_auc']['value']
            }

        # features_json[result['id']['value']] = {
        #     "description": result['description']['value'],
        #     "type": result['embeddingType']['value']
        # }
    return features_json
