import pytest
from fastapi.testclient import TestClient
from gensim.models import KeyedVectors
from openpredict.config import settings
from openpredict.main import app
from openpredict.models.evidence_path import (
    do_evidence_path,
    getQuantiles,
    percentiles_of_different_features,
)
from openpredict.rdf_utils import init_triplestore
from openpredict.utils import init_openpredict_dir
from reasoner_validator import validate

# Create and start Flask from openapi.yml before running tests
init_openpredict_dir()

client = TestClient(app)


def dont_test_get_evidence_path():
    """Test predict API GET operation for a drug"""

    drug_id = "DRUGBANK:DB00915"
    disease_id = "OMIM:104300"
    url = f'/evidence_path?drug_id={drug_id}&disease_id={disease_id}'
    response = client.get(url).json()
    assert len(response['output']) >= 1



def dont_test_do_evidence_path():

    drug_id = "DRUGBANK:DB00915"
    disease_id = "OMIM:104300"
    threshold = 1
    feature_drug = "TC"
    feature_disease = "HPO_SIM"

    assert (do_evidence_path(drug_id=drug_id, disease_id=disease_id,threshold_drugs=threshold, 
                            threshold_disease= threshold,features_drug=feature_drug, features_disease=feature_disease ) is not None)




def dont_test_get_quantiles(): 

        drug_emb = KeyedVectors.load_word2vec_format(
        'openpredict/data/embedding/feature_specific_embeddings_KG/feature_FeatureTypesDrugs.' + "GO_SIM" + '.txt', binary=False)

        disease_emb = KeyedVectors.load_word2vec_format(
        'openpredict/data/embedding/feature_specific_embeddings_KG/feature_FeatureTypesDiseases.' + "HPO_SIM" + '.txt', binary=False)

        assert getQuantiles(drug_emb, disease_emb, 0.5) <= 0.7 

