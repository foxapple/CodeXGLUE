#   Copyright 2015 Ufora Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import unittest
import time
import ufora.native.FORA as ForaNative
import ufora.FORA.python.FORA as FORA
import ufora.cumulus.test.InMemoryCumulusSimulation as InMemoryCumulusSimulation
import ufora.distributed.S3.InMemoryS3Interface as InMemoryS3Interface
import ufora.distributed.S3.ActualS3Interface as ActualS3Interface
import ufora.native.CallbackScheduler as CallbackScheduler
import ufora.test.PerformanceTestReporter as PerformanceTestReporter
import ufora.FORA.python.Runtime as Runtime

callbackScheduler = CallbackScheduler.singletonForTesting()

class MsdbPerformanceTest(unittest.TestCase):
    def computeUsingSeveralWorkers(self, *args, **kwds):
        return InMemoryCumulusSimulation.computeUsingSeveralWorkers(*args, **kwds)

    def dataGenerationScript(self, rowCount, columnCount, seed = 22232425):
        return ("""
let generateNormals = fun(count:, seed:) {
    let it = iterator(math.random.Normal(0, 10, seed));
    [pull it for _ in sequence(count)]
    }
let generateData = fun(nSamples, nFeatures, seed:) {
    let featuresDf = dataframe.DataFrame(
        Vector.range(
            nFeatures,
            { generateNormals(count: nSamples, seed: seed + _) }
            )
        );
    let responseDf = dataframe.DataFrame(
        [generateNormals(count: nSamples, seed: seed + nFeatures)]
        );
    (featuresDf, responseDf)
    };

generateData(%s, %s, seed: %s);
            """ % (rowCount, columnCount, seed)
            )

    def regressionScript(self, maxDepth, nBoosts):
        return """
            math.ensemble.gradientBoosting.GradientBoostedRegressorBuilder(
                nBoosts: %s,
                maxDepth: %s
                );
        """ % (nBoosts, maxDepth)

    def gbmRegressionFittingTest(self, nRows, nColumns, depth, nThreads, nBoosts, copies, report=True):

        s3 = InMemoryS3Interface.InMemoryS3InterfaceFactory()

        result, simulation = InMemoryCumulusSimulation.computeUsingSeveralWorkers(
                        self.dataGenerationScript(nRows, nColumns),
                        s3,
                        1,
                        timeout = 360,
                        memoryLimitMb = 30 * 1024,
                        threadCount = nThreads,
                        returnSimulation = True,
                        useInMemoryCache = False
                        )
        try:
            self.assertTrue(result.isResult())

            dfPredictors, dfResponse = result.asResult.result

            builder = simulation.compute(
                self.regressionScript(depth, nBoosts),
                timeout = 360,
                dfResponse = dfResponse,
                dfPredictors = dfPredictors
                ).asResult.result


            t0 = time.time()

            testName = self.getTestName(nRows, nColumns, depth, nBoosts, nThreads, copies)

            result = simulation.compute(
                "Vector.range(%s).apply(fun(x) { builder.fit(dfPredictors[,-x-1], dfResponse[,-x-1]) })"
                    % copies,
                timeout = 360,
                builder=builder,
                dfPredictors=dfPredictors,
                dfResponse=dfResponse,
                ).asResult.result
            totalTimeToReturnResult = time.time() - t0

            if report:
                PerformanceTestReporter.recordTest(testName, totalTimeToReturnResult, None)

        finally:
            simulation.teardown()

    def getTestName(self, nRows, nColumns, depth, nBoosts, nThreads, copies):
        return "algorithms.gbm.msdb-bigbox.%sRows_%sCol_Depth%s_%sBoosts_%sThreads_%scopies" % (
            nRows, nColumns, depth, nBoosts, nThreads, copies)

    def test_gbmRegressionFitting(self):
        self.gbmRegressionFittingTest(nRows=100000, nColumns=90, depth=5,nThreads=30,nBoosts=5, copies=1, report=False)
        self.gbmRegressionFittingTest(nRows=1000000, nColumns=90, depth=5,nThreads=30,nBoosts=5, copies=1)
        self.gbmRegressionFittingTest(nRows=1000000, nColumns=90, depth=5,nThreads=30,nBoosts=5, copies=4)

if __name__ == "__main__":
    import ufora.config.Mainline as Mainline
    Mainline.UnitTestMainline([FORA, Runtime])

