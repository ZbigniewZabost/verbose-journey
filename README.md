# Get pictures from kita page

This tool helps scrapping pictures from your kita site and save locally so that they can be backed up.

## how to use

1. `docker build -t verbose-journey .`
2. ```shell
	docker run --rm -t --name verbose-journe
	-e EMIAL="my_paiiigeeee_login@email.com" \
	-e PASSWORD="s3r3tt!" \
	-e BASE_URL="https://paiigeee.mykita.com" \
	-e GROUP_ID="99" \
	-e DAY_FROM="2022-12-31" \
	-e DAY_TO="2022-12-31" \
	-v /home/path/where/i/want/pics/to/be:/data \
	verbose-journey
	```

Parameters:
- `EMAIL` and `PASSWORD` are credentials you use to login to kita page
- `BASE_URL` is kita page base url
- `GROUP_ID` is the group id of your kid
- `DAY_FROM` and `DAY_TO` is the timespan to use, both parameters are inclusive
- `/home/path/where/i/want/pics/to/be` - replace it with real path
