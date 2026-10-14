// Create a text parameter named DataFolder pointing to the generated build directory.
let
    Source = Csv.Document(File.Contents(DataFolder & "/shipment_finance.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"expected_cents", type number}, {"billed_cents", type number}, {"carrier_cost_cents", type number}, {"overdue_cents", type number}, {"revenue_gap_cents", type number}}, "en-US")
in
    Typed
