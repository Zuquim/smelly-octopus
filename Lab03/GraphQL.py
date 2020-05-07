from csv import writer
from json import dumps
from requests import post
import time

headers = {"Authorization": "token 09bc2ae56b5a5b7789d725a1aa64f679bd178ad6"}

repositoriesQuery = """
query repositoriesQuery{
  search(type: REPOSITORY, query: "language:python", first: 100{AFTER}) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        ... on Repository {
          id
          nameWithOwner
          url
          stargazers {
            totalCount
          }
          issues {
            totalCount
          }
        }
      }
    }
  }
}
"""

issuesQuery = """
query example {
  repository(owner: "{OWNER}", name: "{NAME}"){
    issues(first: 100, orderBy:{field: CREATED_AT, direction: ASC}{AFTERCURSOR}){
  	  pageInfo{
        hasNextPage
        endCursor
      }
      nodes {
        id
        title
        createdAt
        closedAt
        closed
      }
    }    
  }
}
"""

def runQuery(query):
    request = post(
        'https://api.github.com/graphql', json={'query': query}, headers=headers
    )
    while (request.status_code == 502):
        time.sleep(2)
        request = post(
            'https://api.github.com/graphql', json={'query': query}, headers=headers
        )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query falhou! Codigo de retorno: {}. {}".format(request.status_code, query))

def getAllRepositories(query):
	finalQuery = query.replace("{AFTER}", "")
	results = runQuery(finalQuery)

	totalPages = 1
	currentEndCursor = results["data"]["search"]["pageInfo"]["endCursor"]
	hasNextPage = results["data"]["search"]["pageInfo"]["hasNextPage"]
	allResults = results["data"]["search"]["edges"]

	while hasNextPage and totalPages < 10:
		finalQuery = query.replace("{AFTER}", ', after: "%s"' % currentEndCursor)
		results = runQuery(finalQuery)

		for result in results["data"]["search"]["edges"]:
			allResults.append(result)

		totalPages += 1
		hasNextPage = results["data"]["search"]["pageInfo"]["hasNextPage"]
		currentEndCursor = results["data"]["search"]["pageInfo"]["endCursor"]

	print(dumps(allResults, indent=4, sort_keys=True))

	with open("repositories.csv", "w", newline = '') as file:
	    csv = writer(file)
	    for repo in allResults:
	        csv.writerow(repo["node"].values())

def getAllIssues(issuesQuery):
	with open("repositories.csv", "r", encoding="utf-8") as f:
		lines = f.read()
		for line in lines.splitlines():
			line = line.replace('"', '').split(",")
			nameWithOwner = line[1].split("/")

			owner = nameWithOwner[0]
			name = nameWithOwner[1]

			finalQuery = issuesQuery.replace("{OWNER}", owner).replace("{NAME}", name).replace("{AFTERCURSOR}", "")
			result = runQuery(finalQuery)
			allResults = result["data"]["repository"]["issues"]["nodes"]

			# allResults = getRepositoryIssues(owner, name)

			print(dumps(allResults, indent=4, sort_keys=True))

			try:
				with open("issues.csv", "a", newline = '', encoding="utf-8") as csv_file:
					csv = writer(csv_file)
					for issue in allResults:
						csv.writerow([line[0], issue.values()])
			except Exception as e: 
				print(e)

def getRepositoryIssues(owner, name):
	finalQuery = issuesQuery.replace("{OWNER}", owner).replace("{NAME}", name).replace("{AFTERCURSOR}", "")
	result = runQuery(finalQuery)

	totalPages = 1
	currentEndCursor = result["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
	hasNextPage = result["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]
	allResults = result["data"]["repository"]["issues"]["nodes"]

	while hasNextPage and totalPages < 10:
		finalQuery = issuesQuery.replace("{OWNER}", owner).replace("{NAME}", name).replace("{AFTERCURSOR}", "")
		result = runQuery(finalQuery)
		allResults += result["data"]["repository"]["issues"]["nodes"]

		totalPages += 1
		currentEndCursor = result["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
		hasNextPage = result["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]

	return allResults 

def main():
 	getAllRepositories(repositoriesQuery)
 	getAllIssues(issuesQuery)

main()