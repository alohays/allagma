from culp.classifier import culp
import numpy
from sklearn.model_selection import train_test_split
import pandas
from pathlib import Path

zoo = numpy.array(pandas.read_csv(Path(__file__).resolve().parents[1] / 'data' / 'zoo.txt', header=None))
data = zoo[:, 1:17].astype(float)
labels = zoo[:, 17] - 1

X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)
for lp in ('CN','AA','RA','CS'):
    prediction = culp(X_train, y_train, X_test, link_predictor='CS', similarity='manhattan', k=2)
    print("Prediction Accuracy for Zoo Dataset (λ={0}) = {1}%".format(lp, round(100 * float(numpy.mean(prediction == y_test)), 2)))
