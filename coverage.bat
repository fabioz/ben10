for %m in (archivist ben10 clikit gitit terraforming txtout xml_factory) (
  set COVERAGE_MODULE=%m
  set COVERAGE_PATH=source\python\%m
  pytest -n8 --cov-report term-missing --cov %COVERAGE_MODULE% %COVERAGE_PATH%
)
