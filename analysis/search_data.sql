#Run these queries in athena for Q3

Average searches per day
select avg(count) as average_searches_per_day from (select log_date,count(distinct search_query) as count from domain_search.search_detail
where
log_date >= '2024-07-01' and log_date <= '2024-09-30'
group by log_date
order by log_date) a;


Average visitors per day
select avg(count) from (select log_date,count(distinct visitor_guid) as count from domain_search.search_detail
where
log_date >= '2024-07-01' and log_date <= '2024-09-30'
group by log_date
order by log_date) a;



Average visitors who purchased domains per day
select avg(count) from (select log_date,count(distinct visitor_guid) as count from domain_search.search_detail
where
log_date >= '2024-07-01' and log_date <= '2024-09-30'
and domains_added_to_order_qty > 0
group by log_date
order by log_date) a;




Average gcr per day
select avg(count) from (select log_date,sum(gcr_usd_amt) as count from domain_search.search_detail
where
 log_date >= '2024-07-01' and log_date <= '2024-09-30'
and domains_added_to_order_qty > 0
group by log_date
order by log_date) a;



Based on our concept of Image Search & Entropy & Length less or greater than 5 characters
WITH
search_query_count AS (
    SELECT
        search_query,
        log_date,
        'query1' AS source
    FROM domain_search.search_detail
    WHERE
        log_date >= '2024-07-01' AND log_date <= '2024-09-30'
        AND search_query_tld IS NULL
        AND domains_added_to_order_qty IS NULL
        AND LENGTH(REGEXP_REPLACE(search_query, '(.)(?=.*\\1)', '')) > 25
),
distinct_searches AS (
    SELECT
        search_query,
        log_date,
        'query2' AS source
    FROM domain_search.search_detail
    WHERE
        log_date >= '2024-07-01' AND log_date <= '2024-09-30'
        AND (LENGTH(search_query) <= 5 OR LENGTH(search_query) > 50)
        AND domains_added_to_order_qty IS NULL
        AND search_query_tld IS NULL
),
token_searches AS (
    SELECT
        search_query,
        log_date,
        'query3' AS source
    FROM domain_search.search_detail t
    CROSS JOIN UNNEST(t.token_array) AS u(token)
    WHERE
        log_date >= '2024-07-01' AND log_date <= '2024-09-30'
        AND (
            search_query LIKE '%image%'
            OR search_query LIKE '%pic%'
            OR search_query LIKE '%icon%'
            OR search_query LIKE '%photo%'
            OR search_query LIKE '%graph%'
            OR search_query LIKE '%vision%'
            OR search_query LIKE '%video%'
            OR search_query LIKE '%poster%'
            OR search_query LIKE '%logo%'
            OR search_query LIKE '%symbol%'
            OR search_query LIKE '%domain%'
            OR search_query LIKE '%instagram%'
            OR search_query LIKE '%web%'
            OR search_query LIKE '%idea%'
            OR search_query LIKE '%business%'
            OR search_query LIKE '%design%'
            OR search_query LIKE '%ai%'
            OR search_query LIKE '%artificial intelligence%'
            OR search_query LIKE '%subdomain%'
            OR search_query LIKE '%url%'
            OR search_query LIKE '%industry%'
            OR search_query LIKE '%category%'
            OR search_query LIKE '%e%commerce%'
            OR search_query LIKE '%commerce%'
            OR search_query LIKE '%e-commerce%'
        )
        AND token IN (
            'image','pic','icon','photo','graph','vision','poster','video',
            'logo','symbol','domain','instagram','web','idea','business',
            'design','ai','intelligence','subdomain','url','industry',
            'category','ecommerce','e-commerce','commerce'
        )
        AND search_query_tld IS NULL
        AND domains_added_to_order_qty IS NULL
),
combined_data AS (
    SELECT DISTINCT search_query, log_date
    FROM search_query_count
    UNION
    SELECT DISTINCT search_query, log_date
    FROM distinct_searches
    UNION
    SELECT DISTINCT search_query, log_date
    FROM token_searches
),
daily_search_counts AS (
    SELECT
        log_date,
        COUNT(*) AS total_searches
    FROM combined_data
    GROUP BY log_date
)
SELECT
    AVG(total_searches) AS average_searches_per_day
FROM daily_search_counts;


Looking at Q3 data, we have the following insights:

average searches per day : 1,105,254
average visitor per day : 468,122
average visitors who purchased a domain per day : 21,945
average gcr per day: 987,562
Average searches per day having keywords such as image / general inquires / high level of entropy : 51,945
 GCR rate per search = Avg GCR per day / average searches per day = 987,562/ 1,105,254 ~= 89.35%  Potential increase on helping additional 51,745 searches = 51,945 * .8935 ~ 46,414


* Average GCR per day = 987,562 (this represents the total revenue per day)
* Average searches per day = 1,105,254
* Additional searches = 51,945
* Assuming Conversion improvement with Pixel Insight Recommender Model = 3%
* Additional revenue = 51,945 * 3% = 1,558.35
* Total revenue = 987,562 + 1,558.35 = 989,120.35
* Total revenue per day = 989,120.35
* Total revenue per month = 989,120.35 * 30 = 29,673,610.5
* Total revenue per quarter = 29,673,610.5 * 3 = 89,020,831.5





