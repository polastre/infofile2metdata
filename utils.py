STATES = [x.lower() for x in ["Alabama","Alaska","Arizona","Arkansas","California","Colorado",
  "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois",
  "Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
  "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana",
  "Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York",
  "North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
  "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah",
  "Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"]]

COUNTRIES = [x.lower() for x in [
    "Austria",
    "Australia",
    "France",
    "Germany",
    "Italy",
    "Mexico",
    "Scotland",
    "United Kingdom",
]]

NORMALIZE = {
    'bela fleck and the flecktones': 'Bela Fleck and The Flecktones',
    'bfft': 'Bela Fleck and The Flecktones',
    'dave matthews band': 'Dave Matthews Band',
    'dmb': 'Dave Matthews Band',
    'dave matthews & tim reynolds': 'Dave Matthews and Tim Reynolds',
    'dave matthews and tim reynolds': 'Dave Matthews and Tim Reynolds',
    'pat mcgee band': 'Pat McGee Band',
    'pmb': 'Pat McGee Band',
}
