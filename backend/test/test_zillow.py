from app.services.openwebninja_zillow_api import (
    get_property_details_by_address,
    get_zestimate_from_data,
)


# Replace with a real address
address = "129 Vernon Dr, Bolingbrook, IL 60440"
property_details = get_property_details_by_address(address)
zestimate = get_zestimate_from_data(property_details)

print("Address", address)
print("Response JSON:", zestimate)
