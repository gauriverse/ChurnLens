export const CONTRACTS = ['Month-to-month', 'One year', 'Two year']

export const RISK_CATEGORIES = ['Low', 'Medium', 'High']

export const SOURCE_LABELS = {
    out_of_fold_train: 'Estimated by a cross-validated model that did not see this customer during training',
  holdout_test: 'Estimated by a model that never saw this customer (held-out data)',
  new_data: 'Estimated for a customer scored after the model was trained',
}