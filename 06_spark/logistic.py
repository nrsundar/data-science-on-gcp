from pyspark.mllib.classification import LogisticRegressionWithLBFGS
from pyspark.mllib.regression import LabeledPoint
from pyspark import SparkContext

sc = SparkContext('local', 'logistic')

# read in list of training days
traindays = sc.textFile('gs://cloud-training-demos/flights/trainday.csv') \
              .filter(lambda line: 'True' in line) \
              .map(lambda line: line.split(',')) \
              .map(lambda fields: fields[0])
traindays = set(traindays.collect()) # for fast searching

# read the data, filtering it to keep only traindays and non-cancels
# the header is organically removed because FL_DATE is not a trainday
#allfields = sc.textFile('gs://cloud-training-demos/flights/201501.csv') \
allfields = sc.textFile('gs://cloud-training-demos/flights/2015*.csv') \
           .map(lambda line : line.split(',')) \
           .filter(lambda fields: fields[0] in traindays ) \
           .filter(lambda fields: fields[23] != 'Yes' and fields[22] != '')

# these are the fields we'll use in the regression
# format is LabeledPoint(label, [x1, x2, ...]) 
flights = allfields.map(lambda fields: LabeledPoint(\
              float(float(fields[22]) < 15), #ontime \
              [ \
                  float(fields[15]), # DEP_DELAY \
                  float(fields[16]), # TAXI_OUT \
                  float(fields[26]), # DISTANCE \
              ]))

#flights.saveAsTextFile('gs://cloud-training-demos/flights/sparkoutput/train')

lrmodel = LogisticRegressionWithLBFGS.train(flights, intercept=True)
print lrmodel.weights,lrmodel.intercept

# how good is the fit?
labelpred = flights.map(lambda p: (p.label, lrmodel.predict(p.features)))
def compute_error(labelpred):
    total = labelpred.count()
    wrong = labelpred.filter(lambda (label, pred): label != pred).count()
    return float(wrong)/total
print compute_error(labelpred)

lrmodel.save(sc, 'gs://cloud-training-demos/flights/sparkoutput/model')