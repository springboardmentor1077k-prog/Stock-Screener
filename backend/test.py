from quarterly_compiler import build_last_n_quarters_subquery

sql = build_last_n_quarters_subquery(
    metric="net_profit",
    operator=">",
    value=0,
    n_quarters=4
)

print(sql)
