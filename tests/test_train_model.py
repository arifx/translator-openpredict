import pytest
from openpredict.predict_model_omim_drugbank import train_omim_drugbank_classifier

def test_train_omim_drugbank_classifier():
    """Test the model to get drug-disease similarities (drugbank-omim)"""
    clf, scores = train_omim_drugbank_classifier()

    assert 0.80 < scores['precision'] < 0.95
    assert 0.60 < scores['recall'] < 0.80
    assert 0.80 < scores['accuracy'] < 0.95
    assert 0.85 < scores['roc_auc'] < 0.95
    assert 0.70 < scores['f1'] < 0.85
    assert 0.80 < scores['average_precision'] < 0.95
