from io import BytesIO
from pathlib import Path

from compare_csv import CSV
from flask import url_for
import pytest


metaboanalyst_dir_path = Path(__file__).parent / 'metaboanalyst'


def upload_and_transform(client,
                         filename: str,
                         normalization: str = None,
                         normalization_arg: str = None,
                         transformation: str = None,
                         scaling: str = None) -> str:
    """Upload the given CSV and apply the specified normalization, transformation, and scaling."""
    # Load original data source
    with open(metaboanalyst_dir_path / filename, 'rb') as csv_file:
        file_data = csv_file.read()
    data = {
        'file': (BytesIO(file_data), filename, 'text/csv'),
    }

    # Upload CSV
    resp = client.post(
        url_for('csv.upload_csv_file'), data=data, content_type='multipart/form-data')
    assert resp.status_code == 201
    csv_id = resp.json['id']

    # Validate CSV
    resp = client.post(url_for('csv.save_validated_csv_file', csv_id=csv_id))
    assert resp.status_code == 201

    # Set normalization method to Sum
    resp = client.put(url_for('csv.set_normalization_method', csv_id=csv_id),
                      json={'method': normalization, 'argument': normalization_arg})
    assert resp.status_code == 200

    # Set transformation method to Cube Root
    resp = client.put(url_for('csv.set_transformation_method', csv_id=csv_id),
                      json={'method': transformation, 'argument': None})
    assert resp.status_code == 200

    # Set scaling method to Pareto
    resp = client.put(url_for('csv.set_scaling_method', csv_id=csv_id),
                      json={'method': scaling, 'argument': None})
    assert resp.status_code == 200

    return csv_id


def download_csv(client, csv_id):
    """Download processed CSV"""
    resp = client.get(
        url_for('csv.download_validated_csv_file', csv_id=csv_id)
    )
    assert resp.status_code == 200
    assert 'text/csv' in resp.headers['Content-Type']

    # with open(metaboanalyst_dir_path / 'viime.csv', 'wb') as oot:
    #     oot.write(resp.data)

    return CSV(resp.data.decode('utf-8').strip().split('\n'))


"""
TODO Reference sample normalization works differently in Metaboanalyst
Metaboanalyst (https://github.com/xia-lab/MetaboAnalystR/blob/master/R/general_norm_utils.R):
# normalize by a reference sample (probability quotient normalization)
# ref should be the name of the reference sample
ProbNorm<-function(x, ref.smpl){
    x/median(as.numeric(x/ref.smpl), na.rm=T)
}
VIIME (normalization.py):
def reference_sample(table: pd.DataFrame, argument) -> pd.DataFrame:
    return table.loc[argument].sum() * table.div(table.sum(axis=1), axis=0)
"""

"""
TODO Log transformation works differently in Metaboanalyst
Metaboanalyst (https://github.com/xia-lab/MetaboAnalystR/blob/master/R/general_norm_utils.R):
# generalize log, tolerant to 0 and negative values
LogNorm<-function(x, min.val){
    log2((x + sqrt(x^2 + min.val^2))/2)
}
VIIME (transformation.py):
def log2(table: pd.DataFrame, min=1e-8):
    return np.log(table.clip(lower=min)) / np.log(2)
"""


@pytest.mark.parametrize('expected_csv_filename,transform_kwargs', [
    ('metaboanalyst_normalization_sum.csv', {'normalization': 'sum'}),
    # ('metaboanalyst_normalization_reference_sample_PIF_178.csv', {
    # 'normalization': 'reference-sample', 'normalization_arg': 'PIF_178'}),
    ('metaboanalyst_transformation_cube_root.csv', {'transformation': 'cuberoot'}),
    # ('metaboanalyst_transformation_log.csv', {'transformation': 'log2'}),
    ('metaboanalyst_scaling_auto.csv', {'scaling': 'auto'}),
    ('metaboanalyst_scaling_pareto.csv', {'scaling': 'pareto'}),
    ('metaboanalyst_scaling_range.csv', {'scaling': 'range'}),
])
def test_transformations(client, expected_csv_filename, transform_kwargs):
    csv_id = upload_and_transform(client,
                                  'metaboanalyst_original.csv',
                                  **transform_kwargs)

    actual_csv = download_csv(client, csv_id)

    # Load CSV generated by Metaboanalyst
    with open(metaboanalyst_dir_path / expected_csv_filename, 'r', newline='') as expected_file:
        expected_csv = CSV(expected_file)

    assert actual_csv == expected_csv
