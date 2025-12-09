FROM curlimages/curl:latest

USER root
RUN apk add --no-cache bash

COPY import-dashboards.sh /import-dashboards.sh
RUN chmod +x /import-dashboards.sh

COPY dashboards/*.ndjson /dashboards/

CMD ["/bin/bash", "/import-dashboards.sh"]
