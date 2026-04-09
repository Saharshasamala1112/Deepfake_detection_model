from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

def compute_metrics(labels, preds, outputs):
    accuracy = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds)
    auc = roc_auc_score(labels, outputs)

    return accuracy, f1, auc