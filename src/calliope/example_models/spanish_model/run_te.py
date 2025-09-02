import calliope
print(calliope.__file__)
print('hello')
calliope.set_log_verbosity('INFO')

# Safe save: Commits on Aug 21, 2025
#spanish_model = calliope.Model(r'C:\Users\1496051\PycharmProjects\Calliope_ESP\Spanish model\spanish_model\model.yaml')
#model = calliope.examples.spanish_model()
model = calliope.examples.spanish_model(scenario="monetary_testing")
model.build()
model.solve()

