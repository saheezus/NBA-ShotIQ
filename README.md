Used libraries/packages:

- numpy
- pandas
- nba_api
- json
- scipy
- plotly
- flask

Installations:

- pip install numpy
- pip install pandas
- pip install nba_api
- pip install scipy
- pip install plotly
- pip install flask

Running:

In root directory run command:
- flask run

My project is called NBA ShotIQ, and can be used as a visualization tool for NBA players' shooting accuracy. It takes data collected from the NBA api available on GitHub (https://github.com/swar/nba_api) and generates a 3D surface map, depicting how players' shooting performances differ by each region of the court, such as layups, 3-point shots, and mid-range. Moreover, the graph is entirely interactive, so the user can drag, zoom, hover and click to interact with the graph and see all of its beauty entirely.

Of course, the software behind the graph's visualization and interactiveness are not built by me. The work I've done is use Python and data science libraries such as Pandas, Scipy, and Numpy to carefully extract menaingful shooting data from the dataset. This was done by

1. organizing where each player's shot was taken from on the court, gathered through X and Y coordinates (0 - 500) in the dataset.
2. creating a dictionary to organize each of those shot locations into 10x10 squares
3. combining all of the squres together to form a grid of 2500 total 10x10 squares
4. calculating how many shots made out of total attempts in each grid square
5. using that to generate z data, or how high the graph is at certain points
6. plot everything using a library called plotly, which can create graphs that can be embedded in HTML

It was a great learning process to work with Numpy and Pandas, especially since these are two of the most popular data science libraries out for Python. It also helps that these are being extensively used in machine learning, so I feel like I can apply my skills elsewhere through my experience working with these libraries in this project.

All of the heavylifting was done by plotly, which handles the conversion of the graph to HTML and retains the interactivity of the graph. The process of choosing the right library was actually a little frustrating, due to the fact that previously I had tried with matplotlib. The only problem was, matplotlib couldn't be carried out into a front-end environment like HTML with significant effort, which actually was where I spent a few days just trying. Even when it did get converted to HTML, it didn't retain the interactivess, which I felt was too singificant to sacrifice.

It was also easy that the graph could be easily modified through JSON data. In my app.py file, I passed in many parameters, such as lighting, axis labels, and more, just to make it as aesthetic as possible. It really helped that I could first edit the plotly graph on their website (https://plotly.com/) and figure out what parts to edit.

With a HTML-friendly graph, I was able to use Flask to route the homepage and handle GET and POST requests. The user could type in whatever player's name, and with a few seconds of loading, will be able to generate a completely unique graph of the player's shooting data. This brings the complexity of Python and large data to a user-friendly interface.

At first I struggled to display the HTML content generated by plotly, as the graph was converted to a string version of HTML. However, after looking online for a bit, I found a way to use Jinja and convert the string into raw html to be rendered on the index.html homepage.

Here's a picture of the homepage:

![Alt text](Homepage.jpg?raw=true "Homepage")

For example, Lebron's shooting chart:

![Alt text](Lebron.jpg?raw=true "Lebron")

And from above:

![Alt text](Lebrontop.jpg?raw=true "Lebrontop")