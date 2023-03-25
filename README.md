# Get pictures from kita page

This tool helps to scrap pictures from your kita site and save locally so that they can be backed up.

## How to use

```shell
docker build -t verbose-journey .
docker run --rm -t --name verbose-journey \
-e EMAIL="my_paiiigeeee_login@email.com" \
-e PASSWORD="s3r3tt!" \
-e BASE_URL="https://paiigeee.mykita.com" \
-e GROUP_ID="99" \
-e DAY_FROM="2022-12-31" \
-e DAY_TO="2022-12-31" \
-v /home/path/where/i/want/pics/to/be:/data \
verbose-journey
```

Parameters:
- `EMAIL` and `PASSWORD` are credentials you use to log in to kita page
- `BASE_URL` is kita page base url
- `GROUP_ID` is the group id of your kid
- `DAY_FROM` and `DAY_TO` is the timespan to use, both parameters are optional and inclusive. If not provided `DAY_TO` will be set to current date and `DAY_FROM` to current day minus 7 days
- `/home/path/where/i/want/pics/to/be` - replace it with real path


Docker images are produced with GitHub actions, see packages page.