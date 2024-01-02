from flask import Flask, render_template
from datetime import datetime, timedelta
import random
from openai import OpenAI
import os
from pytz import timezone
import requests
from bs4 import BeautifulSoup

def generate_file_name(directory, base_name, extension):
    # Initialize counter
    counter = 1
    while True:
        # Construct the file name
        file_name = f"{base_name}{counter}.{extension}"
        # Check if the file already exists in the directory
        if not os.path.exists(os.path.join(directory, file_name)):
            return file_name
        # Increment counter if the file exists
        counter += 1
        
app = Flask(__name__)


def pageexists(date):
  url = f'https://www.boxofficemojo.com/date/{date}/'
  # Make a request to the webpage
  response = requests.get(url)

  # Check if the request was successful
  if response.status_code == 200:
      # Parse the HTML content of the webpage
      soup = BeautifulSoup(response.content, 'html.parser')
      
      # Find all elements with class 'mojo-gutter'
      elements = soup.find_all('p', class_='mojo-gutter')
      
      # Check if any element with the class 'mojo-gutter' contains the text 'No data available.'
      found = any(element.get_text(strip=True) == 'No data available.' for element in elements)
      
      if found:
          print("exists")
          return True
      else:
          return False
  else:
      return False

def download_image(url, folder_name):
    # Create a folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Get the image file name from the URL
    image_name = os.path.join(folder_name, generate_file_name("images", "image", "png"))
    
    # Send a GET request to download the image
    response = requests.get(url)
    
    # Save the image to the specified folder
    with open(image_name, 'wb') as file:
        file.write(response.content)
    
    return image_name

def movie_list():
  # Get today's date
  date = datetime.today()
  while True:
     if not pageexists(date.strftime('%Y-%m-%d')):
        break
     else:
        date -= timedelta(days=1)
  print(date.strftime('%Y-%m-%d'))
  url = f"https://www.boxofficemojo.com/date/{date.strftime('%Y-%m-%d')}/"
  response = requests.get(url)
  
  soup = BeautifulSoup(response.content, 'html.parser')
  
  # Find the table containing movie information
  table = soup.find('table', class_='a-bordered')
  
  # Initialize variables to store movie data
  movies_data = []
  
  # Loop through rows in the table and extract data for top 5 movies
  for row in table.find_all('tr')[1:6]:  # Skipping the header row and getting the top 5 movies
      cells = row.find_all('td')
      rank = cells[0].text.strip()
      title = cells[2].text.strip()
      weekend_gross = cells[3].text.strip()
      total_gross = cells[8].text.strip()
  
      # Store movie data in a dictionary
      movie_info = {
          'Rank': rank,
          'Title': title,
          'Daily Gross': weekend_gross,
          'Total Gross': total_gross
      }
      movies_data.append(movie_info)
  
  # Generating HTML to display the scraped movie data with the requested format
  html_output = f"<h2>Top 5 Movies</h2><p>{date.strftime('%B %d')}</p><ol>"
  for movie in movies_data:
      html_output += f"<li><strong>{movie['Title']}</strong><br>{movie['Total Gross']}    +{movie['Daily Gross']}</li>"
  html_output += '</ol>'
  return html_output

def poem():
  # Make a request to the API
  url = "https://poetrydb.org/author/Emily%20Dickinson"
  response = requests.get(url)

  # Check if the request was successful
  if response.status_code == 200:
      # Parse the JSON response
      poems = response.json()
      
      if poems:
          while True:
            # Select a random poem from the list
            random_poem = random.choice(poems)
            
            # Get the title and lines of the poem
            title = random_poem['title']
            lines = random_poem['lines']
            if len(lines) <= 10:
                print("qualifies")
                break
            
          # Create an HTML file to display the poem
          html_content = f"""
          <h2>{title}</h2>
          <p>Emily Dickinson</p>
          <p>{"<br>".join(lines)}</p>
          """

          return html_content
      
def dalle3(prompt):
  # Replace YOUR_API_KEY with your OpenAI API key
  client = OpenAI(api_key = os.environ.get('OPENAI_KEY'))

  # Call the API
  response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
  )
  return download_image(response.data[0].url, "images")

def quote():
  response = requests.get("https://api.quotable.io/random")
  data = response.json()
  return data
with app.app_context():
  print(f"<h2>{datetime.today().strftime('%B %d')}</h2>")
  quote=quote()
  html_content = render_template('main.html', title=datetime.now(timezone('Asia/Seoul')).strftime('%B %d'),Part1=f"<image src='{dalle3('van gogh art seamlessly integrated into real life')}'>", Part3=f'<p>{quote["content"]}<br>- {quote["author"]}</p>',Part4=movie_list(), Part2=poem(), Part5='<h2>Notes</h2>', Part6=f"<h1>{datetime.now(timezone('Asia/Seoul')).strftime('%B %d')}</h1><image src='{dalle3('retro surrealism, digital art')}'>")

file_path = 'index.html'  # Specify the file path where you want to save the HTML file

with open(file_path, 'w') as file:
    file.write(html_content)

print(f"HTML file '{file_path}' has been created.")
