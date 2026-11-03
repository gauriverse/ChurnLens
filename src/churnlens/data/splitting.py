from sklearn.model_selection import train_test_split

from churnlens.features.preprocessing import FEATURES, TARGET

def split_data(df, test_size=0.2,random_state=42):
    """Stratifies train/test split"""
    X = df[FEATURES]
    y = df[TARGET]
    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )